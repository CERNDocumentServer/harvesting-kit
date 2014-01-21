import re
import sys
import time
import traceback
from htmlentitydefs import name2codepoint

from datetime import datetime
from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_OXFORD_DOWNLOADDIR, CFG_ETCDIR,
                            CFG_TMPSHAREDDIR)
from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from ftplib import FTP
from os import listdir, rename, fdopen, pardir
from os.path import join, walk, exists, abspath, basename
from invenio.scoap3utils import (create_logger,
                                 progress_bar,
                                 NoNewFiles,
                                 check_pkgs_integrity)
from invenio.nlm_utils import NLMParser
from shutil import copyfile
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from xml.dom.minidom import parse
from zipfile import ZipFile
from invenio.oup_config import (CFG_LOGIN,
                                CFG_PASSWORD,
                                CFG_URL)

CFG_SCOAP3DTDS_PATH = join(CFG_ETCDIR, 'scoap3dtds')

CFG_OXFORD_JATS_PATH = join(CFG_SCOAP3DTDS_PATH, 'journal-publishing-dtd-2.3.zip')

CFG_TAR_FILES = join(CFG_OXFORD_DOWNLOADDIR, "tar_files")
CFG_UNPACKED_FILES = join(CFG_OXFORD_DOWNLOADDIR, "unpacked_files")


class OxfordPackage(object):
    """
    This class is specialized in parsing an Oxford package
    and creating a SCOAP3-compatible bibupload containing the original
    PDF, XML, and every possible metadata filled in.

    @param package_name: the path to a tar.gz file to expand and parse
    @param path: the actual path of an already expanded package.

    @note: either C{package_name} or C{path} don't have to be passed to the
    constructor, in this case the Oxford server will be harvested.
    """
    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        try:
            self.ftp = FTP(CFG_URL)
            self.ftp.login(user=CFG_LOGIN, passwd=CFG_PASSWORD)
            self.logger.debug("Succesful connection to the Oxford server")
        except:
            self.logger.error("Faild to connect to the Oxford server.")

    def _get_file_listing(self, phrase=None, new_only=True):
        try:
            self.ftp.pwd()
        except Exception, err:
            raise

        if phrase:
            self.files_list = filter(lambda x: phrase in x, self.ftp.nlst())
        else:
            self.files_list = self.ftp.nlst()
        if new_only:
            self.files_list = set(self.files_list) - set(listdir(CFG_TAR_FILES))
        return self.files_list

    def _download_tars(self, check_integrity=True):
        self.retrieved_packages_unpacked = []
        # Prints stuff
        if self.files_list and 'go.xml' in self.files_list:
            ## If no 'go.xml' is there than we skip the task.
            if check_integrity:
                check_pkgs_integrity(self.files_list, self.logger, self.ftp)

            print >> sys.stdout, "\nDownloading %i tar packages." \
                                  % (len(self.files_list))
            # Create progrss bar
            p_bar = progress_bar(len(self.files_list))
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()
            prefix = time.strftime("%Y%m%d%H%M%S-")
            for filename in self.files_list:
                self.logger.info("Downloading tar package: %s" % (filename,))
                unpack_path = join(CFG_TAR_FILES, prefix + filename)
                self.retrieved_packages_unpacked.append(unpack_path)
                try:
                    tar_file = open(unpack_path, 'wb')
                    self.ftp.retrbinary('RETR %s' % filename, tar_file.write)
                    tar_file.close()
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
        self.logger = create_logger("Oxford")

        if not path and package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_packages()
        elif not path and not package_name:
            print "Starting harves"
            self.run()
        self._crawl_oxford_and_find_main_xml()

    def run(self):
        self.connect()
        self._get_file_listing(".zip")
        try:
            self._download_tars()
        except NoNewFiles:
            return
        self._extract_packages()

    def _extract_packages(self):
        """
        Extract a package in a new directory.
        """
        if not hasattr(self, "retrieved_packages_unpacked"):
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
            package_name = basename(path)
            self.path_unpacked = join(CFG_UNPACKED_FILES, package_name.split('.')[0])
            self.logger.debug("Extracting package: %s" % (path.split("/")[-1],))
            try:
                if "_archival_pdf" in self.path_unpacked:
                    self.path_unpacked = self.path_unpacked.rstrip("_archival_pdf")
                    ZipFile(path).extractall(join(self.path_unpacked, "archival_pdfs"))
                else:
                    ZipFile(path).extractall(self.path_unpacked)
                #TarFile.open(path).extractall(self.path_unpacked)
            except Exception, err:
                register_exception(alert_admin=True, prefix="OUP error extracting package.")
                self.logger.error("Error extraction package file: %s" % (path,))
                print >> sys.stdout, "\nError extracting package file: %s" % (path,)

        return self.path_unpacked

    def _crawl_oxford_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in agiven directory.
        """
        self.found_articles = []

        def visit(arg, dirname, names):
            files = [filename for filename in names if ".xml" in filename]
            if files:
                try:
                    for f in files:
                        self.found_articles.append(join(dirname, f))

                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)

        if hasattr(self,'path_unpacked'):
            walk(self.path_unpacked, visit, None)
        elif self.path:
            walk(self.path, visit, None)
        else:
            self.logger.info("Nothing to do.")
            print >> sys.stdout, "Nothing to do."

    def bibupload_it(self):
        if self.found_articles:
            nlm_parser = NLMParser()
            self.logger.debug("Preparing bibupload.")
            fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
            out = fdopen(fd, 'w')
            print >> out, "<collection>"
            for i, path in enumerate(self.found_articles):
                try:
                    print >> out, nlm_parser.get_record(path, publisher='Oxford', collection='SCOAP3', logger=self.logger)
                except Exception, err:
                    print >> sys.stderr, err
                    raise Exception
                print path, i + 1, "out of", len(self.found_articles)
            print >> out, "</collection>"
            out.close()
            task_low_level_submission("bibupload", "admin", "-N" "OUP", "-i", "-r", name)

    def empty_ftp(self):
        if self.found_articles:
            self.logger.info("Finishing UP. Emptying the FTP")
            for filename in self.files_list:
                self.logger.debug("Deleting %s" % filename)
                self.ftp.delete(filename)


def main():
    try:
        if len(sys.argv) == 2:
            path_or_package = sys.argv[1]
            if path_or_package.endswith(".zip"):
                els = OxfordPackage(package_name=path_or_package)
            else:
                print "Try passing a ZIP file."
                #els = OxfordPackage(path=path_or_package)
        else:
            els = OxfordPackage()
        els.bibupload_it()
        els.empty_ftp()
    except Exception, err:
        register_exception()
        print >> sys.stderr, "ERROR: Exception captured: %s" % err
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
