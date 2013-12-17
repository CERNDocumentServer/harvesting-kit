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
                                 progress_bar)
from invenio.nlm_utils import NLMParser
from shutil import copyfile
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from xml.dom.minidom import parse
from zipfile import ZipFile
# from invenio.oxford_config import (CFG_LOGIN,
#                                    CFG_PASSWORD,
#                                    CFG_URL)

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
            self.ftp.cwd('data/in/EPJC/SCOAP3_sample')
        except:
            raise Exception

        if phrase:
            self.files_list = filter(lambda x: phrase in x, self.ftp.nlst())
        else:
            self.files_list = self.ftp.nlst()
        if new_only:
            self.files_list = set(self.files_list) - set(listdir(CFG_OXFORD_DOWNLOADDIR))
        return self.files_list

    # def _download_tars(self):
    #     self.retrieved_packages_unpacked = []
    #     # Prints stuff
    #     print >> sys.stdout, "\nDownloading %i tar packages." \
    #                          % (len(self.files_list))
    #     # Create progrss bar
    #     p_bar = progress_bar(len(self.files_list))
    #     # Print stuff
    #     sys.stdout.write(p_bar.next())
    #     sys.stdout.flush()

    #     for filename in self.files_list:
    #         self.logger.info("Downloading tar package: %s" % (filename,))
    #         unpack_path = join(CFG_TAR_FILES, filename)
    #         self.retrieved_packages_unpacked.append(unpack_path)
    #         try:
    #             tar_file = open(unpack_path, 'wb')
    #             self.ftp.retrbinary('RETR %s' % filename, tar_file.write)
    #             tar_file.close()
    #         except:
    #             self.logger.error("Error downloading tar file: %s" % (filename,))
    #             print >> sys.stdout, "\nError downloading %s file!" % (filename,)
    #             print >> sys.stdout, sys.exc_info()
    #         # Print stuff
    #         sys.stdout.write(p_bar.next())
    #         sys.stdout.flush()

    #     return self.retrieved_packages_unpacked

    def __init__(self, package_name=None, path=None):
        self.package_name = package_name
        self.path = path
        self._dois = []
        self.articles_normalized = []
        self.logger = create_logger("Oxford")

        if not path or package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_packages()
            print >> sys.stdout, self.path
        # elif not path and not package_name:
        #     print "Starting harves"
        #     self.run()
        self._crawl_oxford_and_find_main_xml()
        print >> sys.stdout, self.found_articles, self.articles_normalized

    # def run(self):
    #     self.connect()
    #     self._get_file_listing()
    #     self._download_tars()
    #     self._extract_packages()

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
                TarFile.open(path).extractall(self.path_unpacked)
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
        self.normalized_articles = []

        def visit(arg, dirname, names):
            files = [filename for filename in names if ".xml" in filename]
            if files:
                try:
                    for f in files:
                        self.found_articles.append(join(dirname, f))

                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)

        if self.path_unpacked:
                walk(self.path_unpacked, visit, None)
        else:
            walk(self.path, visit, None)

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
                except:
                    pass
                print path, i + 1, "out of", len(self.found_articles)
            print >> out, "</collection>"
            out.close()
            task_low_level_submission("bibupload", "admin", "-N" "OUP", "-i", "-r", name)


def main():
    try:
        if len(sys.argv) == 2:
            path_or_package = sys.argv[1]
            if path_or_package.endswith(".tar.gz"):
                els = OxfordPackage(package_name=path_or_package)
            else:
                els = OxfordPackage(path=path_or_package)
        else:
            els = OxfordPackage()
        els.bibupload_it()
    except Exception, err:
        register_exception()
        print >> sys.stderr, "ERROR: Exception captured: %s" % err
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
