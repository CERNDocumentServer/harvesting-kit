import sys
import traceback

from datetime import datetime
from invenio.config import (CFG_LOGDIR, CFG_SPRINGER_DOWNLOADDIR, CFG_ETCDIR)
from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from os import listdir, rename
from os.path import join, walk, exists
from scoap3utils import create_logger
from tarfile import TarFile
from tempfile import mkdtemp
from zipfile import ZipFile
CFG_SCOAP3DTDS_PATH = join(CFG_ETCDIR, 'scoap3dtds')

CFG_SPRINGER_AV24_PATH = join(CFG_SCOAP3DTDS_PATH, 'A++V2.4.zip')


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
    def __init__(self, package_name=None, path=None):
        self.package_name = package_name
        self.path = path
        print >> sys.stderr, "aa"
        self.logger = create_logger(join(CFG_LOGDIR, 'springer_harvesting_'+str(datetime.now())+'.log'))

        if not path and package_name:
            print >> sys.stderr, "bb"
            self.path = self._extract_package()
        # elif not path and not package_name:
        #     print "Starting harves"
        #     from invenio.contrast_out import ContrastOutConnector
        #     self.conn = ContrastOutConnector(self.logger)
        #     self.conn.run()
        print >> sys.stderr, "cc"
        self._crawl_springer_and_find_main_xml()
        #self._crawl_springer_and_find_issue_xml()
        #self._build_doi_mapping()

    def bibupload_it(self):
        pass

    def _extract_package(self):
        """
        Extract a package in a new directory.
        """
        print >> sys.stderr, "dd"
        self.path_unpacked = mkdtemp(prefix="scoap3_package_", dir=CFG_SPRINGER_DOWNLOADDIR)
        if not hasattr(self, "retrieved_packages_unpacked"):
            print >> sys.stderr, "e"
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
            print >> sys.stderr, "f"
            ZipFile(path).extractall(self.path_unpacked)

        return self.path_unpacked

    def _crawl_springer_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in agiven directory.
        """
        self.found_articles = []
        # if not self.path and not self.package_name:
        #     for doc in self.conn.found_articles:
        #         dirname = doc['xml'].rstrip('/main.xml')
        #         try:
        #             self._normalize_article_dir_with_dtd(dirname)
        #             self.found_articles.append(dirname)
        #         except Exception, err:
        #             register_exception()
        #             print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
        # else:
        def visit(arg, dirname, names):
            if [filename for filename in names if ".xml.meta" in filename]:
                try:
                    self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
        walk(self.path, visit, None)

    def _crawl_springer_and_find_issue_xml(self):
        pass

    def _normalize_article_dir_with_dtd(self, path):
        """
        main.xml from Elsevier assume the existence of a local DTD.
        This procedure install the DTDs next to the main.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        files = [filename for filename in listdir(path) if ".xml.meta" in filename]
        if exists(join(path, 'resolved_main.xml')):
            return
        # Add looking for a xml.meta file
        # if 'art520' in open(join(path, 'main.xml')).read():
        ZipFile(CFG_SPRINGER_AV24_PATH).extractall(path)
        # for filename in listdir(join(path, '')):
        #     print >> sys.stderr, filename
        #     rename(join(path, 'A++V2.4', filename), join(path, filename))
        #else:
        #    self.logger.error("It looks like the path %s does not contain an art520 or art501 main.xml file" % path)
        #    raise ValueError("It looks like the path %s does not contain an art520 or art501 main.xml file" % path)

        print >> sys.stdout, join(path, files[0])
        print >> sys.stdout, join(path, 'resolved_main.xml')
        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, files[0]), join(path, 'resolved_main.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'main.xml'), cmd_err))


    def _build_doi_mapping(self):
        pass


def main():
    try:
        if len(sys.argv) == 2:
            path_or_package = sys.argv[1]
            if path_or_package.endswith(".tar") or path_or_package.endswith(".zip"):
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
