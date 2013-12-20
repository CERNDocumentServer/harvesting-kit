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


class APPParser(object):
    def __init__(self):
        self.references = None
        self._dois = []

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
            except:
                print >> sys.stderr, "Can't find doi"
                raise Exception

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
            return [get_value_in_tag(keyword) for keyword in xml.getElementsByTagName("Keyword")]
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

    def get_record(self, f_path, publisher=None, collection=None, logger=None):
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
        logger.info("Creating record: %s %s" % (path, doi))
        authors = self.get_authors(xml)
        first_author = True
        for author in authors:
            subfields = [('a', '%s, %s' % (author['surname'], author.get('given_name') or author.get('initials')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('v', aff))
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
        #record_add_field(rec, 'FFT', subfields=[('a', f_path.replace(".xml.Meta", ".pdf"))])
        record_add_field(rec, 'FFT', subfields=[('a', f_path)])
        record_add_field(rec, '980', subfields=[('a', collection), ('b', publisher)])
        return record_xml_output(rec)
