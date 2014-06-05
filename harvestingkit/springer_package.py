# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2013, 2014 CERN.
##
## Harvesting Kit is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Harvesting Kit is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
import sys
import traceback
from datetime import datetime
from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_PREFIX,
                            CFG_TMPSHAREDDIR)
from os.path import (join,
                     walk,
                     exists)
try:
    from invenio.config import CFG_SPRINGER_DOWNLOADDIR
except ImportError:
    CFG_SPRINGER_DOWNLOADDIR = join(CFG_PREFIX, "var", "data" "scoap3" "springer")

from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from os import (listdir,
                fdopen)
from harvestingkit.scoap3utils import (create_logger,
                                       progress_bar,
                                       NoNewFiles)
from harvestingkit.jats_utils import JATSParser
from harvestingkit.app_utils import APPParser
from tempfile import (mkdtemp,
                      mkstemp)
from zipfile import ZipFile
from invenio.springer_config import (CFG_LOGIN,
                                     CFG_PASSWORD,
                                     CFG_URL)
from harvestingkit.ftp_utils import FtpHandler
from harvestingkit.config import CFG_DTDS_PATH as CFG_SCOAP3DTDS_PATH

CFG_SPRINGER_AV24_PATH = join(CFG_SCOAP3DTDS_PATH, 'A++V2.4.zip')
CFG_SPRINGER_JATS_PATH = join(CFG_SCOAP3DTDS_PATH, 'jats-archiving-dtd-1.0.zip')

CFG_TAR_FILES = join(CFG_SPRINGER_DOWNLOADDIR, "tar_files")


class SpringerPackage(object):
    """
    This class is specialized in parsing an Springer package
    and creating a SCOAP3-compatible bibupload containing the original
    PDF, XML, and every possible metadata filled in.

    @param package_name: the path to a tar.gz file to expand and parse
    @param path: the actual path of an already expanded package.

    @note: either C{package_name} or C{path} don't have to be passed to the
    constructor, in this case the Springer server will be harvested.
    """
    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        try:
            self.ftp = FtpHandler(CFG_URL, CFG_LOGIN, CFG_PASSWORD)
            self.logger.debug("Succesful connection to the Springer server")
        except:
            self.logger.error("Faild to connect to the Springer server.")

    def _get_file_listing(self, phrase=None, new_only=True):
        self.jhep_list = []
        self.epjc_list = []
        self.files_list = []
        if phrase:
            self.epjc_list.extend(filter(lambda x: phrase in x and ".zip" in x, self.ftp.ls("data/in/EPJC")[0]))
            self.jhep_list.extend(filter(lambda x: phrase in x and ".zip" in x, self.ftp.ls("data/in/JHEP")[0]))
        else:
            self.epjc_list.extend(filter(lambda x: ".zip" in x, self.ftp.ls("data/in/EPJC")[0]))
            self.jhep_list.extend(filter(lambda x: ".zip" in x, self.ftp.ls("data/in/JHEP")[0]))

        self.files_list.extend(map(lambda x: "data/in/EPJC/"+x, self.epjc_list))
        self.files_list.extend(map(lambda x: "data/in/JHEP/"+x, self.jhep_list))

        if new_only:
            tmp_our_dir = []
            try:
                tmp_our_dir.extend(map(lambda x: "data/in/EPJC/"+x, listdir(join(CFG_TAR_FILES, "data/in/EPJC"))))
            except OSError:  # folders does not exists nothing to do
                pass
            try:
                tmp_our_dir.extend(map(lambda x: "data/in/JHEP/"+x, listdir(join(CFG_TAR_FILES, "data/in/JHEP"))))
            except OSError:  # folders does not exists nothing to do
                pass
            self.files_list = set(self.files_list) - set(tmp_our_dir)
        return self.files_list

    def _download_tars(self, check_integrity=True):
        self.retrieved_packages_unpacked = []
        # Prints stuff
        if self.files_list:
            if check_integrity:
                self.ftp.check_pkgs_integrity(self.files_list, self.logger)

            print >> sys.stdout, "\nDownloading %i tar packages." \
                                 % (len(self.files_list))
            # Create progrss bar
            p_bar = progress_bar(len(self.files_list))
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

            for filename in self.files_list:
                self.logger.info("Downloading tar package: %s" % (filename,))
                unpack_path = join(CFG_TAR_FILES, filename)
                self.retrieved_packages_unpacked.append(unpack_path)
                try:
                    self.ftp.download(filename, CFG_TAR_FILES)
                except:
                    self.logger.error("Error downloading tar file: %s" % (filename,))
                    print >> sys.stdout, "\nError downloading %s file!" % (filename,)
                    print >> sys.stdout, sys.exc_info()
                # Print stuff
                sys.stdout.write(p_bar.next())
                sys.stdout.flush()

            return self.retrieved_packages_unpacked
        else:
            print >> sys.stdout, "No new packages to download."
            self.logger.info("No new packages to download.")
            raise NoNewFiles

    def __init__(self, package_name=None, path=None):
        self.package_name = package_name
        self.path = path
        self._dois = []
        self.articles_normalized = []
        self.logger = create_logger("Springer")

        if not path and package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_packages()
        elif not path and not package_name:
            print "Starting harvest"
            self.run()
        self._crawl_springer_and_find_main_xml()

    def run(self):
        self.connect()
        self._get_file_listing()
        try:
            self._download_tars()
        except NoNewFiles:
            return
        self._extract_packages()

    def _extract_packages(self):
        """
        Extract a package in a new directory.
        """
        self.path_unpacked = []
        if not hasattr(self, "retrieved_packages_unpacked"):
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
            self.logger.debug("Extracting package: %s" % (path,))

            if 'EPJC' in path:
                self.path_unpacked.append(mkdtemp(prefix="scoap3_package_%s_EPJC_" % (datetime.now(),),
                                                  dir=CFG_TMPSHAREDDIR))
            else:
                self.path_unpacked.append(mkdtemp(prefix="scoap3_package_%s_JHEP_" % (datetime.now(),),
                                                  dir=CFG_TMPSHAREDDIR))
            try:

                ZipFile(path).extractall(self.path_unpacked[-1])
            except Exception:
                register_exception(alert_admin=True, prefix="Springer error extracting package.")
                self.logger.error("Error extraction package file: %s" % (path,))
                print >> sys.stdout, "\nError extracting package file: %s" % (path,)

        return self.path_unpacked

    def _crawl_springer_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in agiven directory.
        """
        self.found_articles = []

        def visit(arg, dirname, names):
            files = [filename for filename in names if "nlm.xml" in filename]
            if not files:
                files = [filename for filename in names if ".xml.scoap" in filename]
            if files:
                try:
                    # self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)

        if hasattr(self, 'path_unpacked'):
            for path in self.path_unpacked:
                walk(path, visit, None)
        elif self.path:
            walk(self.path, visit, None)
        else:
            self.logger.info("Nothing to do.")
            print >> sys.stdout, "Nothing to do."

    def _normalize_article_dir_with_dtd(self, path):
        """
        TODO: main.xml from Springer assume the existence of a local DTD.
        This procedure install the DTDs next to the main.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        files = [filename for filename in listdir(path) if "nlm.xml" in filename]
        if not files:
                files = [filename for filename in listdir(path) if ".xml.scoap" in filename]
        if exists(join(path, 'resolved_main.xml')):
            return

        if 'JATS-archivearticle1.dtd' in open(join(path, files[0])).read():
            path_normalized = mkdtemp(prefix="scoap3_normalized_jats_", dir=CFG_TMPSHAREDDIR)
            ZipFile(CFG_SPRINGER_JATS_PATH).extractall(path_normalized)
        elif 'A++V2.4.dtd' in open(join(path, files[0])).read():
            path_normalized = mkdtemp(prefix="scoap3_normalized_app_", dir=CFG_TMPSHAREDDIR)
            ZipFile(CFG_SPRINGER_AV24_PATH).extractall(path_normalized)
        else:
            self.logger.error("It looks like the path %s does not contain an JATS-archivearticle1.dtd nor A++V2.4.dtd XML file." % path)
            raise ValueError("It looks like the path %s does not contain an JATS-archivearticle1.dtd nor A++V2.4.dtd XML file." % path)
        print >> sys.stdout, "Normalizing %s" % (files[0],)
        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, files[0]), join(path_normalized, 'resolved_main.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'main.xml'), cmd_err))
        self.articles_normalized.append(path_normalized)

    def bibupload_it(self):
        # if self.articles_normalized:
        #     self.logger.debug("Preparing bibupload.")
        #     fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
        #     out = fdopen(fd, 'w')
        #     print >> out, "<collection>"
        #     for i, path in enumerate(self.articles_normalized):
        #         try:
        #             if "jats" in path:
        #                 jats_parser = JATSParser()
        #                 print >> out, jats_parser.get_record(join(path, "resolved_main.xml"), publisher='Springer', collection='SCOAP3', logger=self.logger)
        #             else:
        #                 app_parser = APPParser()
        #                 print >> out, app_parser.get_record(join(path, "resolved_main.xml"), publisher='SISSA', collection='SCOAP3', logger=self.logger)
        #             print path, i + 1, "out of", len(self.found_articles)
        #         except Exception, err:
        #             self.logger.error("Error creating record from: %s \n%s" % (join(path, 'resolved_main.xml'), err))
        #     print >> out, "</collection>"
        #     out.close()
        #     task_low_level_submission("bibupload", "admin", "-N", "Springer", "-i", "-r", name)
        if self.found_articles:
            self.logger.debug("Preparing bibupload.")
            fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
            out = fdopen(fd, 'w')
            print >> out, "<collection>"
            for i, path in enumerate(self.found_articles):
                try:
                    if "EPJC" in path:
                        for filename in listdir(path):
                            if "_nlm.xml" in filename:
                                jats_parser = JATSParser(tag_to_remove="tex-math")
                                print >> out, jats_parser.get_record(join(path, filename), publisher='Springer', collection='SCOAP3', logger=self.logger)
                    else:
                        for filename in listdir(path):
                            if ".xml.scoap" in filename:
                                app_parser = APPParser()
                                print >> out, app_parser.get_record(join(path, filename), publisher='SISSA', collection='SCOAP3', logger=self.logger)
                    print path, i + 1, "out of", len(self.found_articles)
                except Exception, err:
                    register_exception(alert_admin=True)
                    self.logger.error("Error creating record from: %s \n%s" % (join(path, filename), err))
            print >> out, "</collection>"
            out.close()
            task_low_level_submission("bibupload", "admin", "-N", "Springer", "-i", "-r", name)


def main():
    try:
        if len(sys.argv) == 2:
            path_or_package = sys.argv[1]
            if path_or_package.endswith(".zip"):
                els = SpringerPackage(package_name=path_or_package)
            else:
                els = SpringerPackage(path=path_or_package)
        else:
            els = SpringerPackage()
        els.bibupload_it()
    except Exception, err:
        register_exception()
        print >> sys.stderr, "ERROR: Exception captured: %s" % err
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
