import re
import sys
import time
import traceback

from os import listdir, rename, fdopen, pardir
from os.path import join, walk, exists, abspath

from invenio.bibrecord import record_add_field, record_xml_output
from invenio.errorlib import register_exception
from invenio.minidom_utils import (get_value_in_tag,
                                   xml_to_text,
                                   NoDOIError,
                                   format_arxiv_id)
from xml.dom.minidom import parse


class JATSParser(object):
    def __init__(self):
        self.references = None

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
        doi = self.get_doi(art)

        return (journal, issn, volume, issue, first_page, last_page, year, doi)

    def get_doi(self, xml):
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
            text = re.sub(r'^(\d+\ ?)', "", xml_to_text(affiliation))
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
            return get_value_in_tag(xml, "copyright-holder")
        except Exception, err:
            print >> sys.stderr, "Can't find copyright"

    def get_keywords(self, xml):
        try:
            kwd_groups = xml.getElementsByTagName('kwd-group')
            pacs = []
            other = []
            for kwd_group in kwd_groups:
                if kwd_group.getAttribute('kwd-group-type').encode('utf-8') == "pacs":
                    pacs = [xml_to_text(keyword) for keyword in kwd_group.getElementsByTagName("kwd")]
                else:
                    other = [xml_to_text(keyword) for keyword in kwd_group.getElementsByTagName("kwd")]
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

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ref"):
            plain_text = None
            try:
                ref_type = reference.getElementsByTagName('mixed-citation')[0].getAttribute('publication-type').encode('utf-8')
            except:
                ref_type = reference.getElementsByTagName('citation')[0].getAttribute('publication-type').encode('utf-8')
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
            ext_link = format_arxiv_id(self.get_ref_link(reference, "arxiv"))
            if ref_type != 'journal':
                try:
                    plain_text = get_value_in_tag(reference, "mixed-citation")
                except:
                    plain_text = get_value_in_tag(reference, "citation")
            references.append((label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text))
        self.references = references

    def get_record(self, f_path, publisher=None, collection=None, logger=None):
        xml = self.get_article(f_path)
        rec = {}
        title = self.get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        record_add_field(rec, '260', subfields=[('c', time.strftime('%Y-%m-%d'))])
        journal, issn, volume, issue, first_page, last_page, year, doi = self.get_publication_information(xml)

        if logger:
            logger.info("Creating record: %s %s" % (join(f_path, pardir), doi))

        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
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
            record_add_field(rec, '520', subfields=[('a', abstract), ('9', publisher)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'), ('u', 'http://creativecommons.org/licenses/by/3.0/')])
        copyright = self.get_copyright(xml)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = self.get_keywords(xml)
        if keywords['pacs']:
            for keyword in keywords['pacs']:
                record_add_field(rec, '084', ind1='1', subfields=[('a', keyword), ('9', 'PACS')])
        if keywords['other']:
            for keyword in keywords['other']:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        record_add_field(rec, '773', subfields=[('p', journal), ('v', volume), ('n', issue), ('c', '%s-%s' % (first_page, last_page)), ('y', year)])
        self.get_references(xml)
        for label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text in self.references:
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
            if title and volume and year and page:
                subfields.append(('s', '%s %s (%s) %s' % (title, volume, year, page)))
            elif not plain_text:
                subfields.append(('m', ('%s %s %s %s' % (title, volume, year, page))))
            if plain_text:
                subfields.append(('m', plain_text))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
        # record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
        record_add_field(rec, 'FFT', subfields=[('a', f_path)])
        extra_subfields = []
        if collection:
            extra_subfields.append(('a', collection))
        if publisher:
            extra_subfields.append(('b', publisher))
        record_add_field(rec, '980', subfields=extra_subfields)
        return record_xml_output(rec)
