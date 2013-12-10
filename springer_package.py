import sys
import time
import traceback

from datetime import datetime
from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_SPRINGER_DOWNLOADDIR, CFG_ETCDIR,
                            CFG_TMPSHAREDDIR)
from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from ftplib import FTP
from os import listdir, rename, fdopen, pardir
from os.path import join, walk, exists, abspath
from invenio.scoap3utils import (create_logger,
                                 progress_bar)
from invenio.jats_utils import get_record
from shutil import copyfile
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from xml.dom.minidom import parse
from zipfile import ZipFile
from invenio.springer_config import (CFG_LOGIN,
                                     CFG_PASSWORD,
                                     CFG_URL)

CFG_SCOAP3DTDS_PATH = join(CFG_ETCDIR, 'scoap3dtds')

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
            self.ftp = FTP(CFG_URL)
            self.ftp.login(user=CFG_LOGIN, passwd=CFG_PASSWORD)
            self.logger.debug("Succesful connection to the Springer server")
        except:
            self.logger.error("Faild to connect to the Springer server.")

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
            self.files_list = set(self.files_list) - set(listdir(CFG_SPRINGER_DOWNLOADDIR))
        return self.files_list

    def _download_tars(self):
        self.retrieved_packages_unpacked = []
        # Prints stuff
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
            print "Starting harves"
            self.run()
        self._crawl_springer_and_find_main_xml()
        print >> sys.stdout, self.found_articles

    def run(self):
        self.connect()
        self._get_file_listing()
        self._download_tars()
        self._extract_packages()

    def _extract_packages(self):
        """
        Extract a package in a new directory.
        """
        self.path_unpacked = mkdtemp(prefix="scoap3_package_%s_" % (datetime.now(),),
                                     dir=CFG_TMPSHAREDDIR)
        if not hasattr(self, "retrieved_packages_unpacked"):
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
            self.logger.debug("Extracting package: %s" % (path.split("/")[-1],))
            ZipFile(path).extractall(self.path_unpacked)

        return self.path_unpacked

    def _crawl_springer_and_find_main_xml(self):
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
                    self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)

        if self.path_unpacked:
                walk(self.path_unpacked, visit, None)
        else:
            walk(self.path, visit, None)

    def _normalize_article_dir_with_dtd(self, path):
        """
        TODO: main.xml from Springer assume the existence of a local DTD.
        This procedure install the DTDs next to the main.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        path_normalized = mkdtemp(prefix="scoap3_normalized_", dir=CFG_TMPSHAREDDIR)
        self.articles_normalized.append(path_normalized)
        files = [filename for filename in listdir(path) if "nlm.xml" in filename]
        if exists(join(path, 'resolved_main.xml')):
            return

        #print join(path, files[0])
        if 'JATS-archivearticle1.dtd' in open(join(path, files[0])).read():
            ZipFile(CFG_SPRINGER_JATS_PATH).extractall(path_normalized)
        else:
            self.logger.error("It looks like the path %s does not contain an JATS-archivearticle1.dtd XML file." % path)
            raise ValueError("It looks like the path %s does not contain an JATS-archivearticle1.dtd XML file." % path)
        print >> sys.stdout, "Normalizing %s" % (files[0],)
        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, files[0]), join(path_normalized, 'resolved_main.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'main.xml'), cmd_err))


    def bibupload_it(self):
        self.logger.debug("Preparing bibupload.")
        fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
        out = fdopen(fd, 'w')
        print >> out, "<collection>"
        for i, path in enumerate(self.articles_normalized):
            print >> out, get_record(join(path, "resolved_main.xml"), publisher='Springer', repository='SCOAP3', logger=self.logger)
            print path, i + 1, "out of", len(self.found_articles)
        print >> out, "</collection>"
        out.close()
        task_low_level_submission("bibupload", "Elsevier", "-i", "-r", name)


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
