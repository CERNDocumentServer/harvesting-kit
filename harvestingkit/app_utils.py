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

import re
import sys
from os.path import (join,
                     exists)
from harvestingkit.bibrecord import (record_add_field,
                                     create_record,
                                     record_xml_output)
from harvestingkit.utils import add_nations_field
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from xml.dom.minidom import parse

RE_ARXIV_ID = re.compile(r"\d+.\d+")


class APPParser(object):
    def __init__(self, extract_nations=False):
        self.references = None
        self.extract_nations = extract_nations

    def get_doi(self, xml):
        doi = ""
        try:
            doi = get_value_in_tag(xml, "ArticleDOI")
            if not doi:
                print >> sys.stderr, "DOI not found"
        except Exception, err:
            print >> sys.stderr, "Can't find doi: %s" % err
        return doi

    def get_article(self, path):
        return parse(open(path))

    def get_title(self, xml):
        try:
            return get_value_in_tag(xml, "ArticleTitle")
        except Exception:
            print >> sys.stderr, "Can't find title"

    def get_publication_information(self, xml):
        doi = self.get_doi(xml)
        #journal, issn, volume, issue, first_page, last_page, year
        journal = get_value_in_tag(xml, "JournalAbbreviatedTitle")
        if journal == 'J. High Energ. Phys.':
            journal = 'JHEP'
        issn = get_value_in_tag(xml, "JournalAbbreviatedTitle")
        volume = get_value_in_tag(xml, "VolumeIDStart")[2:] + "%02d" % int(get_value_in_tag(xml, "IssueIDStart"))
        issue = ""
        first_page = "%03d" % int(get_value_in_tag(xml, "ArticleSequenceNumber"))
        pages = get_value_in_tag(xml, "ArticleLastPage")
        year = get_value_in_tag(xml, "VolumeIDStart")
        return journal, issn, volume, issue, first_page, pages, year, doi

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
            text = xml_to_text(affiliation, delimiter=', ')
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

    def get_publication_date(self, xml):
        try:
            article_info = xml.getElementsByTagName("ArticleInfo")[0]
            article_history = article_info.getElementsByTagName("ArticleHistory")[0]
            online_date = article_history.getElementsByTagName("OnlineDate")
            if online_date:
                online_date = online_date[0]
                year = get_value_in_tag(online_date, "Year")
                month = get_value_in_tag(online_date, "Month")
                day = get_value_in_tag(online_date, "Day")
                return "%04d-%02d-%02d" % (int(year), int(month), int(day))
        except Exception, err:
            print >> sys.stderr, "Can't reliably extract the publication date: %s" % err
            return ""

    def get_abstract(self, xml):
        try:
            return get_value_in_tag(xml.getElementsByTagName("Abstract")[0], "Para")
        except Exception:
            print >> sys.stderr, "Can't find abstract"

    def get_copyright(self, xml):
        try:
            return get_value_in_tag(xml.getElementsByTagName("ArticleCopyright")[0], "CopyrightHolderName")
        except Exception, err:
            print >> sys.stderr, "Can't find copyright. %s" % (err, )

    def get_keywords(self, xml):
        try:
            return [xml_to_text(keyword) for keyword in xml.getElementsByTagName("Keyword")]
        except Exception, err:
            print >> sys.stderr, "Can't find keywords. %s" % (err,)

    def get_body_ref(self, xml):
        try:
            ref = xml.getElementsByTagName('BodyRef')[0]
            return ref.getAttribute('FileRef').encode('utf-8')
        except Exception:
            print >> sys.stderr, "Can't find reference to XML file."

    def get_arxiv_id(self, xml):
        article_note = xml.getElementsByTagName('ArticleNote')
        if article_note:
            article_note = article_note[0]
        else:
            return ""
        arxiv_id = get_value_in_tag(article_note, "RefSource")
        if RE_ARXIV_ID.match(arxiv_id):
            return "arXiv:%s" % arxiv_id
        return ""

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
        #path = abspath(join(f_path, pardir))
        xml = self.get_article(f_path)
        rec = create_record()
        title = self.get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        publication_date = self.get_publication_date(xml)
        if publication_date:
            record_add_field(rec, '260', subfields=[('c', publication_date)])
        journal, issn, volume, issue, first_page, pages, year, doi = self.get_publication_information(xml)
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        arxiv_id = self.get_arxiv_id(xml)
        if arxiv_id:
            record_add_field(rec, '037', subfields=[('a', arxiv_id), ('9', 'arXiv')])
        if logger:
            logger.info("Creating record: %s %s" % (f_path, doi))
        authors = self.get_authors(xml)
        first_author = True
        for author in authors:
            subfields = [('a', '%s, %s' % (author['surname'], author.get('given_name') or author.get('initials')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('v', aff))

                if self.extract_nations:
                    add_nations_field(subfields)

            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)

        abstract = self.get_abstract(xml)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-4.0'), ('u', 'http://creativecommons.org/licenses/by/4.0/')])
        copyright = self.get_copyright(xml)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = self.get_keywords(xml)
        if keywords:
            for keyword in keywords:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        record_add_field(rec, "300", subfields=[('a', pages)])

        subfields = filter(lambda x: x[1] and x[1] != '-', [('p', journal),
                                                            ('v', volume),
                                                            ('c', first_page),
                                                            ('y', year)])
        record_add_field(rec, '773', subfields=subfields)
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

        folder_name = join('/', *(f_path.split('/')[0:-1]))
        pdf_name = f_path.split('/')[-1].rstrip('.xml.scoap') + '.pdf'
        pdf_path = join(folder_name, 'BodyRef/PDF', pdf_name)
        print pdf_path
        if exists(pdf_path):
            record_add_field(rec, 'FFT', subfields=[('a', pdf_path), ('n', 'main'), ('f', '.pdf;pdfa')])
        else:
            # Don't know why it doesn't work????????????
            # register_exception(alert_admin=True)
            if logger:
                logger.error("Record %s doesn't contain PDF file." % (doi,))
        record_add_field(rec, 'FFT', subfields=[('a', self.get_body_ref(xml)), ('n', 'main')])
        record_add_field(rec, '980', subfields=[('a', collection), ('b', publisher)])
        return record_xml_output(rec)
