import re
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
from ftplib import FTP
from os import listdir, rename, fdopen, pardir
from os.path import join, walk, exists, abspath
from invenio.scoap3utils import (create_logger,
                         get_value_in_tag,
                         xml_to_text,
                         progress_bar,
                         NoDOIError)
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

    def get_article(self, path):
        return parse(open(path))

    def get_title(self, xml):
        try:
            return get_value_in_tag(xml, "article-title")
        except Exception, err:
            print >> sys.stderr, "Can't find title"

    def get_issn(self, xml):
        issns = xml.getElementsByTagName('issn')
        ret = None

        for issn in issns:
            if issn.getAttribute("pub-type").encode('utf-8') == 'epub':
                ret = issn.getAttribute("pub-type").encode('utf-8')

        if not ret and issns:
            ret = xml_to_text(issns[0])

        return ret

    def get_date(self, xml):
        dates = xml.getElementsByTagName('pub-date')
        ret = None
        for date in dates:
            if date.getAttribute('pub-type').encode('utf-8') == 'epub':
                ret = get_value_in_tag(date, 'year')

        if not ret and dates:
            return dates[0]
        else:
            return ret

    def get_publication_information(self, xml):
        jid = get_value_in_tag(xml, "journal-id")
        journal = ""
        #journal = CFG_ELSEVIER_JID_MAP.get(jid, jid)
        try:
            art = xml.getElementsByTagName('article-meta')[0]
        except IndexError, err:
            register_exception()
            print >> sys.stderr, "ERROR: XML corupted: %s" % err
        except Exception, err:
            register_exception()
            print >> sys.stderr, "ERROR: Exception captured: %s" % err

        issn = self.get_issn(art)
        volume = get_value_in_tag(art, "volume")
        issue = get_value_in_tag(art, "issue")
        year = self.get_date(art)
        first_page = get_value_in_tag(art, "fpage")
        last_page = get_value_in_tag(art, "lpage")
        doi = self._get_doi(art)

        return (journal, issn, volume, issue, first_page, last_page, year, doi)

    def _get_doi(self, xml):
        ids = xml.getElementsByTagName('article-id')
        ret = ""
        for i in ids:
            if i.getAttribute('pub-id-type').encode('utf-8') == 'doi':
                ret = xml_to_text(i)

        if not ret:
            print >> sys.stdout, "Can't find DOI."
        return ret

    def get_authors(self, xml):
        authors = []
        for author in xml.getElementsByTagName("contrib"):
            tmp = {}
            surname = get_value_in_tag(author, "surname")
            if surname:
                tmp["surname"] = surname
            given_name = get_value_in_tag(author, "given-names")
            if given_name:
                tmp["given_name"] = given_name.replace('\n', ' ')

            # It's not there
            # orcid = author.getAttribute('orcid').encode('utf-8')
            # if orcid:
            #     tmp["orcid"] = orcid

            # cross_refs = author.getElementsByTagName("ce:cross-ref")
            # if cross_refs:
            #     tmp["cross_ref"] = []
            #     for cross_ref in cross_refs:
            #         tmp["cross_ref"].append(cross_ref.getAttribute("refid").encode('utf-8'))
            tmp["affiliations_ids"] = []
            tmp["contact_ids"] = []

            xrefs = author.getElementsByTagName("xref")
            for x in xrefs:
                if x.getAttribute('ref-type').encode('utf-8') == 'aff':
                    tmp["affiliations_ids"].extend([a.encode('utf-8') for a in x.getAttribute('rid').split()])
                if x.getAttribute('ref-type').encode('utf-8') == 'corresp':
                    tmp["contact_ids"].extend([a.encode('utf-8') for a in x.getAttribute('rid').split()])

            authors.append(tmp)

        affiliations = {}
        for affiliation in xml.getElementsByTagName("aff"):
            aff_id = affiliation.getAttribute("id").encode('utf-8')
            # removes numbering in from affiliations
            text = re.sub(r'^(\d+\ )', "", xml_to_text(affiliation))
            affiliations[aff_id] = text

        emails = {}
        for contact in xml.getElementsByTagName("corresp"):
            contact_id = contact.getAttribute("id").encode('utf-8')
            text = xml_to_text(contact.getElementsByTagName('email')[0])
            emails[contact_id] = text

        implicit_affilations = True
        for author in authors:
            matching_ref = [ref for ref in author.get("affiliations_ids") if ref in affiliations]
            if matching_ref:
                implicit_affilations = False
                author["affiliation"] = []
                for i in xrange(0, len(matching_ref)):
                    author["affiliation"].append(affiliations[matching_ref[i]])
            matching_contact = [cont for cont in author.get('contact_ids') if cont in emails]
            if matching_contact:
                author["email"] = emails[matching_contact[0]]

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
            return get_value_in_tag(xml, "abstract").replace("Abstract", "", 1)
        except Exception, err:
            print >> sys.stderr, "Can't find abstract"

    def get_copyright(self, xml):
        try:
            return get_value_in_tag(xml.getElementsByTagName("copyright-holder")[0])
        except Exception, err:
            print >> sys.stderr, "Can't find copyright"

    def get_keywords(self, xml):
        try:
            kwd_groups = xml.getElementsByTagName('kwd-group')
            pacs = []
            other = []
            for kwd_group in kwd_groups:
                if kwd_group.getAttribute('kwd-group-type').encode('utf-8') == "pacs":
                    pacs = [xml_to_text(keyword) for keyword in xml.getElementsByTagName("kwd")]
                else:
                    other = [xml_to_text(keyword) for keyword in xml.getElementsByTagName("kwd")]
            return {"pacs": pacs, "other": other}
        except Exception, err:
            print >> sys.stderr, "Can't find keywords"

    def get_ref_link(self, xml, name):
        links = xml.getElementsByTagName('ext-link')
        ret = None
        for link in links:
            if name in link.getAttribute("xlink:href").encode('utf-8'):
                ret = xml_to_text(link).strip()
        return ret

    def format_arxiv_id(self, arxiv_id):
        if arxiv_id and not "/" in arxiv_id and "arXiv" not in arxiv_id:
            return "arXiv:%s" % (arxiv_id,)
        else:
            return arxiv_id

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ref"):
            plain_text = None
            ref_type = reference.getElementsByTagName('mixed-citation')[0].getAttribute('publication-type').encode('utf-8')
            label = get_value_in_tag(reference, "label").strip('.')
            authors = []
            for author in reference.getElementsByTagName("name"):
                given_name = get_value_in_tag(author, "given-names")
                surname = get_value_in_tag(author, "surname")
                if given_name:
                    name = "%s, %s" % (surname, given_name)
                else:
                    name = surname
                if name.strip().split() == []:
                    name = get_value_in_tag(author, "string-name")
                authors.append(name)
            doi_tag = reference.getElementsByTagName("pub-id")
            doi = ""
            for tag in doi_tag:
                if tag.getAttribute("pub-id-type") == "doi":
                    doi = xml_to_text(tag)
            issue = get_value_in_tag(reference, "issue")
            page = get_value_in_tag(reference, "fpage")
            page_last = get_value_in_tag(reference, "lpage")
            title = get_value_in_tag(reference, "source")
            volume = get_value_in_tag(reference, "volume")
            year = get_value_in_tag(reference, "year")
            ext_link = self.format_arxiv_id(self.get_ref_link(reference, "arxiv"))
            if ref_type != 'journal':
                plain_text = get_value_in_tag(reference, "mixed-citation")
            references.append((label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text))
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
        self.logger.info("Creating record: %s %s" % (path, doi))
        authors = self.get_authors(xml)
        first_author = True
        for author in authors:
            if author.get('surname'):
                subfields = [('a', '%s, %s' % (author.get('surname'), author.get('given_name') or author.get('initials', '')))]
            else:
                subfields = [('a', '%s' % (author.get('name', '')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('v', aff))
            if author.get('email'):
                    subfields.append(('m', author['email']))
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
        if keywords['pacs']:
            for keyword in keywords:
                record_add_field(rec, '084', ind1='1', subfields=[('a', keyword), ('9', 'PACS')])
        if keywords['other']:
            for keyword in keywords:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        record_add_field(rec, '773', subfields=[('p', journal), ('v', volume), ('n', issue), ('c', '%s-%s' % (first_page, last_page)), ('y', year)])
        references = self.get_references(xml)
        for label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text in references:
            subfields = []
            if doi:
                subfields.append(('a', doi))
            for author in authors:
                subfields.append(('h', author))
            if issue:
                subfields.append(('n', issue))
            if label:
                subfields.append(('o', label))
            if year:
                subfields.append(('y', year))
            if ext_link:
                subfields.append(('r', ext_link))
            # should we be strict about it?
            if title and volume and year:
                subfields.append(('s', '%s %s (%s) %s' % (title, volume, year, page)))
            if plain_text:
                subfields.append(('m', plain_text))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
        # record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
        record_add_field(rec, 'FFT', subfields=[('a', f_path)])
        record_add_field(rec, '980', subfields=[('a', 'SCOAP3'), ('b', 'Springer')])
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
