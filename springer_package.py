import sys
import time
import traceback

from datetime import datetime
from functools import partial
from invenio.bibrecord import record_add_field, record_xml_output
from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_SPRINGER_DOWNLOADDIR, CFG_ETCDIR,
                            CFG_TMPSHAREDDIR)
from invenio.errorlib import register_exception
from invenio.shellutils import run_shell_command
from os import listdir, rename, fdopen, pardir
from os.path import join, walk, exists, abspath
from scoap3utils import (create_logger, get_value_in_tag, xml_to_text)
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from xml.dom.minidom import parse
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
        self._dois = []
        self.articles_normalized = []
        self.logger = create_logger("Springer")

        if not path and package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_package()
        # elif not path and not package_name:
        #     print "Starting harves"
        #     from invenio.contrast_out import ContrastOutConnector
        #     self.conn = ContrastOutConnector(self.logger)
        #     self.conn.run()
        self._crawl_springer_and_find_main_xml()

    def _extract_package(self):
        """
        Extract a package in a new directory.
        """
        self.path_unpacked = mkdtemp(prefix="scoap3_package_%s" % (datetime.now(),),
                                     dir=CFG_TMPSHAREDDIR)
        self.logger.debug("Extracting package: %s" % (self.package_name,))
        if not hasattr(self, "retrieved_packages_unpacked"):
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
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
            files = [filename for filename in names if ".xml.meta" in filename]
            if files:
                try:
                    self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
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
        files = [filename for filename in listdir(path) if ".xml.meta" in filename]
        if exists(join(path, 'resolved_main.xml')):
            return

        if 'A++V2.4.dtd' in open(join(path, files[0])).read():
            ZipFile(CFG_SPRINGER_AV24_PATH).extractall(path_normalized)
        else:
            self.logger.error("It looks like the path %s does not contain an A++V2.4.dtd XML file." % path)
            raise ValueError("It looks like the path %s does not contain an A++V2.4.dtd XML file." % path)
        print >> sys.stdout, "Normalizing %s" % (join(path, files[0]), )
        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, files[0]), join(path_normalized, 'resolved_main.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'main.xml'), cmd_err))

    def get_article(self, path):
        return parse(open(path))

    def get_title(self, xml):
        try:
            return get_value_in_tag(xml, "ArticleTitle")
        except Exception, err:
            print >> sys.stderr, "Can't find title"

    def get_publication_information(self, xml):
        doi = self._get_doi(xml)
        try:
            return self._dois[doi] + (doi, )
        except:
            return ('', '', '', '', '', '', '', doi)

    def _get_doi(self, xml):
        try:
            return get_value_in_tag(xml, "ArticleDOI")
        except Exception, err:
            print >> sys.stderr, "Can't find doi"

    def get_authors(self, xml):
        authors = []
        for author in xml.getElementsByTagName("Author"):
            tmp = {}
            surname = get_value_in_tag(author, "FamilyName")
            if surname:
                tmp["surname"] = surname
            given_name = get_value_in_tag(author, "GivenName")
            if given_name:
                tmp["given_name"] = given_name.replace('\n', ' ')
            # initials = get_value_in_tag(author, "ce:initials")
            # if initials:
            #     tmp["initials"] = initials
            # It's not there
            # orcid = author.getAttribute('orcid').encode('utf-8')
            # if orcid:
            #     tmp["orcid"] = orcid
            emails = author.getElementsByTagName("Email")
            for email in emails:
                if email.getAttribute("type").encode('utf-8') in ('email', ''):
                    tmp["email"] = xml_to_text(email)
                    break
            # cross_refs = author.getElementsByTagName("ce:cross-ref")
            # if cross_refs:
            #     tmp["cross_ref"] = []
            #     for cross_ref in cross_refs:
            #         tmp["cross_ref"].append(cross_ref.getAttribute("refid").encode('utf-8'))
            tmp["affiliations_ids"] = []
            aids = author.getAttribute("AffiliationIDS").split()
            for aid in aids:
                tmp["affiliations_ids"].append(aid.encode('utf-8'))
            authors.append(tmp)
        affiliations = {}
        for affiliation in xml.getElementsByTagName("Affiliation"):
            aff_id = affiliation.getAttribute("ID").encode('utf-8')
            text = xml_to_text(affiliation)
            affiliations[aff_id] = text
        implicit_affilations = True
        for author in authors:
            matching_ref = [ref for ref in author.get("affiliations_ids") if ref in affiliations]
            if matching_ref:
                implicit_affilations = False
                author["affiliation"] = []
                for i in xrange(0, len(matching_ref)):
                    author["affiliation"].append(affiliations[matching_ref[i]])
        if implicit_affilations and len(affiliations) > 1:
            print >> sys.stderr, "Implicit affiliations are used, but there's more than one affiliation: %s" % affiliations
        if implicit_affilations and len(affiliations) >= 1:
            for author in authors:
                author["affiliation"] = []
                for aff in affiliations.values():
                    author["affiliation"].append(aff)
        return authors

    def get_abstract(self, xml):
        try:
            return get_value_in_tag(xml, "Abstract")
        except Exception, err:
            print >> sys.stderr, "Can't find abstract"

    def get_copyright(self, xml):
        try:
            return get_value_in_tag(xml.getElementsByTagName("ArticleCopyright"), "CopyrightHolderName")
        except Exception, err:
            print >> sys.stderr, "Can't find copyright"

    def get_keywords(self, xml):
        try:
            return [get_value_in_tag(keyword, "ce:text") for keyword in xml.getElementsByTagName("ce:keyword")]
        except Exception, err:
            print >> sys.stderr, "Can't find keywords"

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("Citation"):
            if not reference.getElementsByTagName("BibArticle"):
                references.append((get_value_in_tag(reference,
                                                    "BibUnstructured"),
                                   '', '', '', '', '', '', ''))
            else:
                label = get_value_in_tag(reference, "ArticleTitle")
                authors = []
                for author in reference.getElementsByTagName("BibAuthorName"):
                    given_name = get_value_in_tag(author, "Initials")
                    surname = get_value_in_tag(author, "FamilyName")
                    if given_name:
                        name = "%s, %s" % (surname, given_name)
                    else:
                        name = surname
                    authors.append(name)
                doi_tag = reference.getElementsByTagName("Occurrence")
                doi = ""
                for tag in doi_tag:
                    if tag.getAttribute("Type") == "DOI":
                        doi = xml_to_text(tag)
                ## What is it exactly?
                # issue = get_value_in_tag(reference, "sb:issue")
                issue = ""
                page = get_value_in_tag(reference, "FirstPage")
                title = get_value_in_tag(reference, "JournalTitle")
                volume = get_value_in_tag(reference, "VolumeID")
                year = get_value_in_tag(reference, "Year")
                references.append((label, authors, doi, issue, page, title, volume, year))
        return references

    def get_record(self, f_path):
        path = abspath(join(f_path, pardir))
        xml = self.get_article(join(path, "resolved_main.xml"))
        rec = {}
        title = self.get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        record_add_field(rec, '260', subfields=[('c', time.strftime('%Y-%m-%d'))])
        journal, issn, volume, issue, first_page, last_page, year, doi = self.get_publication_information(xml)
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        self.logger.info("Creating record: %s %s" % (path,doi))
        authors = self.get_authors(xml)
        first_author = True
        for author in authors:
            subfields = [('a', '%s, %s' % (author['surname'], author.get('given_name') or author.get('initials')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('u', aff))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        abstract = self.get_abstract(xml)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'), ('u', 'http://creativecommons.org/licenses/by/3.0/')])
        copyright = self.get_copyright(xml)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = self.get_keywords(xml)
        if keywords:
            for keyword in keywords:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        record_add_field(rec, '773', subfields=[('p', journal), ('v', volume), ('n', issue), ('c', '%s-%s' % (first_page, last_page)), ('y', year)])
        references = self.get_references(xml)
        for label, authors, doi, issue, page, title, volume, year in references:
            subfields = []
            if doi:
                subfields.append(('a', doi))
            for author in authors:
                subfields.append(('h', author))
            if issue:
                subfields.append(('n', issue))
            if label:
                subfields.append(('o', label))
            if page:
                subfields.append(('p', page))
            subfields.append(('s', '%s %s (%s) %s' % (title, volume, year, page)))
            if title:
                subfields.append(('t', title))
            if volume:
                subfields.append(('v', volume))
            if year:
                subfields.append(('y', year))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
        # record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
        record_add_field(rec, 'FFT', subfields=[('a', f_path)])
        record_add_field(rec, '980', subfields=[('a', 'SCOAP3')])
        return record_xml_output(rec)

    def bibupload_it(self):
        self.logger.debug("Preparing bibupload.")
        fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
        out = fdopen(fd, 'w')
        print >> out, "<collection>"
        for i, path in enumerate(self.articles_normalized):
            print >> out, self.get_record(join(path, "resolved_main.xml"))
            print path, i + 1, "out of", len(self.found_articles)
        print >> out, "</collection>"
        out.close()
        task_low_level_submission("bibupload", "Elsevier", "-i", "-r", name)


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
