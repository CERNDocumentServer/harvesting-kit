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
import time

from socket import timeout as socket_timeout_exception

from datetime import datetime
from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_PREFIX,
                            CFG_TMPSHAREDDIR,
                            CFG_LOGDIR)
from os.path import (join,
                     walk,
                     exists)
try:
    from invenio.config import CFG_SPRINGER_DOWNLOADDIR
except ImportError:
    CFG_SPRINGER_DOWNLOADDIR = join(CFG_PREFIX, "var", "data",
                                    "scoap3", "springer")

from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from harvestingkit.ftp_utils import FtpHandler
from os import listdir, fdopen
from .scoap3utils import (LoginException,
                          NoNewFiles)
from .jats_utils import JATSParser
from .app_utils import APPParser
from tempfile import mkdtemp, mkstemp
from zipfile import ZipFile

from configparser import load_config

from .config import (CFG_CONFIG_PATH,
                     CFG_DTDS_PATH,
                     CFG_FTP_CONNECTION_ATTEMPTS,
                     CFG_FTP_TIMEOUT_SLEEP_DURATION)

from .utils import create_logger


CFG_SPRINGER_AV24_PATH = join(CFG_DTDS_PATH, 'A++V2.4.zip')
CFG_SPRINGER_JATS_PATH = join(CFG_DTDS_PATH, 'jats-archiving-dtd-1.0.zip')

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
        for tryed_connection_count in range(CFG_FTP_CONNECTION_ATTEMPTS):
            try:
                self.ftp = FtpHandler(self.config.SPRINGER.URL,
                                      self.config.SPRINGER.LOGIN,
                                      self.config.SPRINGER.PASSWORD)
                self.logger.debug(("Successful connection to "
                                   "the Springer server"))
                return
            except socket_timeout_exception as err:
                self.logger.error(('Failed to connect %d of %d times. '
                                   'Will sleep for %d seconds and try again.')
                                  % (tryed_connection_count+1,
                                     CFG_FTP_CONNECTION_ATTEMPTS,
                                     CFG_FTP_TIMEOUT_SLEEP_DURATION))
                time.sleep(CFG_FTP_TIMEOUT_SLEEP_DURATION)
            except Exception as err:
                self.logger.error(("Failed to connect to the "
                                   "Springer server. %s") % (err,))
                break

        raise LoginException(err)

    def _get_file_listing(self, phrase=None, new_only=True):
        self.jhep_list = []
        self.epjc_list = []
        self.files_list = []

        self.ftp.cd('data/in')

        if phrase:
            self.epjc_list.extend(filter(lambda x: phrase in x and ".zip" in x,
                                         self.ftp.ls("EPJC")[0]))
            self.jhep_list.extend(filter(lambda x: phrase in x and ".zip" in x,
                                         self.ftp.ls("JHEP")[0]))
        else:
            self.epjc_list.extend(filter(lambda x: ".zip" in x,
                                         self.ftp.ls("EPJC")[0]))
            self.jhep_list.extend(filter(lambda x: ".zip" in x,
                                         self.ftp.ls("JHEP")[0]))

        self.files_list.extend(map(lambda x: "EPJC/" + x,
                                   self.epjc_list))
        self.files_list.extend(map(lambda x: "JHEP/" + x,
                                   self.jhep_list))

        if new_only:
            tmp_our_dir = []
            for di in ["EPJC/", "JHEP/"]:
                try:
                    tmp_our_dir.extend(map(lambda x: di + x,
                                           listdir(join(CFG_TAR_FILES, di))))
                except OSError:  # folders does not exists nothing to do
                    pass

            self.files_list = set(self.files_list) - set(tmp_our_dir)

        return self.files_list

    def _download_tars(self, check_integrity=True):
        self.retrieved_packages_unpacked = []

        if self.files_list:
            if check_integrity:
                self.ftp.check_pkgs_integrity(self.files_list, self.logger)

            print "Downloading %i tar packages." % (len(self.files_list))

            total_count = len(self.files_list)

            for i, filename in enumerate(self.files_list, start=1):
                self.logger.info("Downloading tar package %s of %s: %s"
                                 % (i, total_count, filename,))
                unpack_path = join(CFG_TAR_FILES, filename)
                self.retrieved_packages_unpacked.append(unpack_path)

                try:
                    self.ftp.download(filename, CFG_TAR_FILES)
                    self.packages_delivery.append((filename[0:-4],
                                                   datetime.now()))
                except:
                    self.logger.error("Error downloading tar file: %s"
                                      % (filename,))
                    print sys.exc_info()

            return self.retrieved_packages_unpacked
        else:
            self.logger.info("No new packages to download.")
            raise NoNewFiles

    def __init__(self, package_name=None, path=None,
                 extract_nations=False):
        self.package_name = package_name
        self.path = path
        self._dois = []
        self.articles_normalized = []
        self.logger = create_logger(
            "Springer",
            filename=join(CFG_LOGDIR, 'scoap3_harvesting.log')
        )

        self.config = load_config(CFG_CONFIG_PATH, {'SPRINGER': []})

        self.packages_delivery = []
        self.doi_package_name_mapping = []

        if not path and package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_packages()
        elif not path and not package_name:
            print "Starting harvest"
            self.run()
        self._crawl_springer_and_find_main_xml()

        self.extract_nations = extract_nations

    def run(self):
        try:
            self.connect()
            self._get_file_listing()
            self._download_tars()
        except LoginException as err:
            error_msg = "Failed to connect to the Springer server. %s" % (err,)
            register_exception(alert_admin=True, prefix=error_msg)
            return
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

            p_name = 'EPJC' if 'EPJC' in path else 'JHEP'
            p_message = 'scoap3_package_%s_%s_' % (p_name, datetime.now())

            self.path_unpacked.append(mkdtemp(prefix=p_message,
                                              dir=CFG_TMPSHAREDDIR))

            try:
                ZipFile(path).extractall(self.path_unpacked[-1])
            except Exception:
                register_exception(alert_admin=True,
                                   prefix="Springer error extracting package.")
                self.logger.error("Error extraction package file: %s"
                                  % (path,))

        return self.path_unpacked

    def _crawl_springer_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in a given directory.
        """
        self.found_articles = []

        def visit(arg, dirname, names):
            files = [filename for filename in names if "nlm.xml" in filename]
            if not files:
                files = [filename for filename in names
                         if ".xml.scoap" in filename]
            if files:
                try:
                    # self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception as err:
                    register_exception()
                    print "ERROR: can't normalize %s: %s" % (dirname, err)

        if hasattr(self, 'path_unpacked'):
            for path in self.path_unpacked:
                walk(path, visit, None)
        elif self.path:
            walk(self.path, visit, None)
        else:
            self.logger.info("Nothing to do.")

    def _normalize_article_dir_with_dtd(self, path):
        """
        TODO: main.xml from Springer assume the existence of a local DTD.
        This procedure install the DTDs next to the main.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        files = [filename for filename in listdir(path)
                 if "nlm.xml" in filename]
        if not files:
                files = [filename for filename in listdir(path)
                         if ".xml.scoap" in filename]
        if exists(join(path, 'resolved_main.xml')):
            return

        if 'JATS-archivearticle1.dtd' in open(join(path, files[0])).read():
            path_normalized = mkdtemp(prefix="scoap3_normalized_jats_",
                                      dir=CFG_TMPSHAREDDIR)
            ZipFile(CFG_SPRINGER_JATS_PATH).extractall(path_normalized)
        elif 'A++V2.4.dtd' in open(join(path, files[0])).read():
            path_normalized = mkdtemp(prefix="scoap3_normalized_app_",
                                      dir=CFG_TMPSHAREDDIR)
            ZipFile(CFG_SPRINGER_AV24_PATH).extractall(path_normalized)
        else:
            error_msg = ("It looks like the path %s does not contain an "
                         "JATS-archivearticle1.dtd nor A++V2.4.dtd XML file.")
            self.logger.error(error_msg % path)
            raise ValueError(error_msg % path)
        print "Normalizing %s" % (files[0],)
        (cmd_exit_code,
         cmd_out,
         cmd_err) = run_shell_command(("xmllint --format "
                                       "--loaddtd %s --output %s"),
                                      (join(path, files[0]),
                                       join(path_normalized,
                                            'resolved_main.xml')))
        if cmd_err:
            error_msg = "Error in cleaning %s: %s"
            self.logger.error(error_msg % (join(path, 'issue.xml'), cmd_err))
            raise ValueError(error_msg % (join(path, 'main.xml'), cmd_err))
        self.articles_normalized.append(path_normalized)

    def bibupload_it(self):
        if self.found_articles:
            self.logger.debug("Preparing bibupload.")
            fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_',
                               dir=CFG_TMPSHAREDDIR)
            out = fdopen(fd, 'w')
            print >> out, "<collection>"
            for i, path in enumerate(self.found_articles):
                try:
                    for filename in listdir(path):

                        if filename.endswith(".xml.scoap"):
                            xml_end = True
                        elif filename.endswith("_nlm.xml"):
                            xml_end = False
                        else:
                            continue

                        l_info = '%s is JHCP' if xml_end else '%s is EPJC'
                        lc_info = 'Found %s. Calling SISSA' if xml_end \
                                  else 'Found %s. Calling Springer'
                        publi = 'SISSA' if xml_end else 'Springer'

                        if xml_end:
                            parser = APPParser(extract_nations=
                                               self.extract_nations)
                        else:
                            parser = JATSParser(extract_nations=
                                                self.extract_nations)

                        self.logger.info(l_info % path)
                        self.logger.info(lc_info % filename)
                        rec = parser.get_record(join(path, filename),
                                                publisher=publi,
                                                collection='SCOAP3',
                                                logger=self.logger)

                        xml_doc = parser.get_article(join(path, filename))
                        doi = parser.get_doi(xml_doc)
                        package_name = [x for x in path.split('/')
                                        if 'scoap3_package' in x]
                        if package_name:
                            doi_name_map = (package_name[0], doi)
                            self.doi_package_name_mapping.append(doi_name_map)

                        print >> out, rec
                        break
                    print path, i + 1, "out of", len(self.found_articles)
                except Exception as err:
                    register_exception(alert_admin=True)
                    self.logger.error("Error creating record from: %s \n%s"
                                      % (join(path, filename), err))
            print >> out, "</collection>"
            out.close()
            task_low_level_submission("bibupload", "admin", "-N",
                                      "Springer", "-i", "-r", name)
