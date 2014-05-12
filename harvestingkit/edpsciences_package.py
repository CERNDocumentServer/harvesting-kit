# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2014 CERN.
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
from __future__ import print_function
import sys
from invenio.refextract_kbs import get_kbs
from invenio.refextract_api import extract_references_from_string_xml
from invenio.bibrecord import (record_add_field,
                               record_xml_output)
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         get_attribute_in_tag,
                                         xml_to_text)
from harvestingkit.utils import (collapse_initials,
                                 fix_journal_name)
from xml.dom.minidom import (parse,
                             parseString)
from datetime import (date,
                      datetime)


class EDPSciencesPackage(object):
    """
    This class is specialized in parsing files from EdpSciences FTP server
    and converting them in Marc XML.
    """

    def __init__(self):
        try:
            self.journal_mappings = get_kbs()['journals'][1]
        except KeyError:
            self.journal_mappings = {}
            return

    def _get_abstract(self):
        try:
            return get_value_in_tag(self.doc, 'abstract')
        except Exception:
            print >> sys.stderr, "Can't find abstract"
            return ''

    def _get_journal_name(self):
        try:
            return get_value_in_tag(self.doc, 'journal-title')
        except Exception:
            print >> sys.stderr, "Can't find journal name"
            return ''

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'article-title')
        except Exception:
            print >> sys.stderr, "Can't find title"
            return ''

    def _get_date(self):
        final = ''
        epub_date = ''
        ppub_date = ''
        for dateTag in self.doc.getElementsByTagName('pub-date'):
            if dateTag.getAttribute('pub-type') == 'final':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    final = str(date(year, month, day))
                except ValueError:
                    pass
            if dateTag.getAttribute('pub-type') == 'epub':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    epub_date = str(date(year, month, day))
                except ValueError:
                    pass
            elif dateTag.getAttribute('pub-type') == 'ppub':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    ppub_date = str(date(year, month, day))
                except ValueError:
                    pass
        if final:
            return final
        elif epub_date:
            return epub_date
        elif ppub_date:
            return ppub_date
        else:
            print >> sys.stderr, "Can't find publication date"
            return datetime.now().strftime("%Y-%m-%d")

    def _get_doi(self):
        for article_id in self.doc.getElementsByTagName('article-id'):
            if article_id.getAttribute('pub-id-type') == 'doi':
                return article_id.firstChild.data

    def _get_emails(self):
        emails = {}
        for tag in self.doc.getElementsByTagName('author-notes'):
            email_elements = tag.getElementsByTagName('corresp')
            email_elements += tag.getElementsByTagName('fn')
            for tg in email_elements:
                noteid = tg.getAttribute('id')
                email = get_value_in_tag(tg, 'email')
                if email:
                    emails[noteid] = email
        return emails

    def _get_authors(self):
        authors = []
        for contrib in self.doc.getElementsByTagName('contrib'):
            if contrib.getAttribute('contrib-type') == 'author':
                surname = get_value_in_tag(contrib, 'surname')
                given_names = get_value_in_tag(contrib, 'given-names')
                given_names = collapse_initials(given_names)
                name = '%s, %s' % (surname, given_names)
                affiliation = ''
                corresp = ''
                for tag in contrib.getElementsByTagName('xref'):
                    if tag.getAttribute('ref-type') == 'aff':
                        affiliation = tag.getAttribute('rid')
                    elif tag.getAttribute('ref-type') == 'corresp':
                        corresp = tag.getAttribute('rid')
                authors.append((name, affiliation, corresp))
        return authors

    def _get_publication_information(self):
        journal = self._get_journal_name()
        date = self._get_date()
        doi = self._get_doi()
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        volume += get_value_in_tag(self.doc, 'volume')
        page = get_value_in_tag(self.doc, 'elocation-id')
        fpage = get_value_in_tag(self.doc, 'fpage')
        lpage = get_value_in_tag(self.doc, 'lpage')
        year = date[:4]
        return (journal, volume, page, year, date, doi, fpage, lpage)

    def _get_affiliations(self):
        affiliations = {}
        for aff in self.doc.getElementsByTagName('aff'):
            affiliations[aff.getAttribute('id')] = xml_to_text(aff)
        return affiliations

    def _add_references(self, rec):
        for ref in self.doc.getElementsByTagName('ref'):
            text_ref = ''
            ext_link = ''
            for mixed in ref.getElementsByTagName('mixed-citation'):
                ref_type = mixed.getAttribute('publication-type')
                if ref_type == 'thesis':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                elif ref_type == 'conf-proc':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                elif ref_type == 'other':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                    ext_link = get_value_in_tag(mixed, 'ext-link')
            authors = []
            for auth in ref.getElementsByTagName('string-name'):
                surname = get_value_in_tag(auth, 'surname')
                given_names = get_value_in_tag(auth, 'given-names')
                given_names = collapse_initials(given_names)
                authors.append('%s, %s' % (surname, given_names))
            year = get_value_in_tag(ref, 'year')
            source = get_value_in_tag(ref, 'source')
            volume = get_value_in_tag(ref, 'volume')
            page = get_value_in_tag(ref, 'fpage')
            subfields = []
            if text_ref:
                ref_xml = extract_references_from_string_xml(text_ref)
                dom = parseString(ref_xml)
                fields = dom.getElementsByTagName("datafield")[0]
                fields = fields.getElementsByTagName("subfield")
                for field in fields:
                    data = field.firstChild.data
                    code = field.getAttribute("code")
                    subfields.append((code, data))
            if ref_type == 'journal':
                source, vol = fix_journal_name(source, self.journal_mappings)
                if vol:
                    volume = vol + volume
            if ref_type:
                subfields.append(('d', ref_type))
            if text_ref:
                subfields.append(('m', text_ref))
            if ext_link:
                subfields.append(('u', ext_link))
            for author in authors:
                subfields.append(('h', author))
            if year:
                subfields.append(('y', year))
            if source and volume and page:
                subfields.append(('s', source + "," + volume + "," + page))
            elif source and volume:
                subfields.append(('s', source + "," + volume))
            elif source and page:
                subfields.append(('s', source + "," + page))
            elif source:
                subfields.append(('s', source))
            record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

    def get_record_rich(self, filename):
        """
        Gets the Marc xml of the files in xaml_rich directory

        :param fileName: the name of the file to parse.
        :type fileName: string

        :returns: a string with the marc xml version of the file.
        """
        self.doc = parse(filename)
        rec = {}
        articles = self.doc.getElementsByTagName('ArticleID')
        for article in articles:
            article_type = article.getAttribute('Type')
            if not article_type == 'Article':
                return ''
            doi = get_value_in_tag(self.doc, 'DOI')
            date = ''
            for tag in self.doc.getElementsByTagName('Accepted'):
                year = get_value_in_tag(tag, 'Year')
                month = get_value_in_tag(tag, 'Month').zfill(2)
                day = get_value_in_tag(tag, 'Day').zfill(2)
                date = "%s-%s-%s" % (year, month, day)
            if not date:
                for tag in self.doc.getElementsByTagName('OnlineDate'):
                    year = get_value_in_tag(tag, 'Year')
                    month = get_value_in_tag(tag, 'Month').zfill(2)
                    day = get_value_in_tag(tag, 'Day').zfill(2)
                    date = "%s-%s-%s" % (year, month, day)
            first_page = get_value_in_tag(article, 'FirstPage')
            last_page = get_value_in_tag(article, 'LastPage')
            subjects = article.getElementsByTagName('Keyword')
            subjects = map(xml_to_text, subjects)
            subject = ', '.join(subjects)
            copyright_statement = get_value_in_tag(article, 'Copyright')
        journal = get_value_in_tag(self.doc, 'JournalTitle')
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        issues = self.doc.getElementsByTagName('IssueID')
        for issue in issues:
            volume += get_value_in_tag(issue, 'Volume')
            year = get_value_in_tag(issue, 'Year')
        title = get_value_in_tag(self.doc, 'Title')
        authors = self.doc.getElementsByTagName('Author')
        affiliations = self.doc.getElementsByTagName('Affiliation')

        def affiliation_pair(a):
            return a.getAttribute('ID'), get_value_in_tag(a, 'UnstructuredAffiliation')

        affiliations = map(affiliation_pair, affiliations)
        affiliations = dict(affiliations)

        def author_pair(a):
            surname = get_value_in_tag(a, 'LastName')
            first_name = get_value_in_tag(a, 'FirstName')
            middle_name = get_value_in_tag(a, 'MiddleName')
            if middle_name:
                name = '%s, %s %s' % (surname, first_name, middle_name)
            else:
                name = '%s, %s' % (surname, first_name)
            try:
                affid = a.getElementsByTagName('AffiliationID')[0].getAttribute('Label')
                affiliation = affiliations[affid]
            except IndexError:
                affiliation = ''
            except KeyError:
                affiliation = ''
            return name, affiliation

        authors = map(author_pair, authors)
        abstract = get_value_in_tag(self.doc, 'Abstract')
        references = self.doc.getElementsByTagName('Bibliomixed')

        for reference in references:
            subfields = []
            label = reference.getAttribute('N')
            if label:
                subfields.append(('o', label))
            bibliosets = reference.getElementsByTagName('Biblioset')
            for tag in bibliosets:
                ref_year = get_value_in_tag(tag, 'Date')
                ref_journal = get_value_in_tag(tag, 'JournalShortTitle')
                ref_journal, ref_volume = fix_journal_name(ref_journal, self.journal_mappings)
                ref_volume += get_value_in_tag(tag, 'Volume')
                ref_page = get_value_in_tag(tag, 'ArtPageNums')
                if ref_year:
                    subfields.append(('y', ref_year))
                if ref_journal and ref_volume and ref_page:
                    subfields.append(('s', '%s,%s,%s' % (ref_journal,
                                                         ref_volume,
                                                         ref_page)))
                reference.removeChild(tag)
            text_ref = xml_to_text(reference)
            ref_xml = extract_references_from_string_xml(text_ref)
            dom = parseString(ref_xml)
            fields = dom.getElementsByTagName("datafield")[0]
            fields = fields.getElementsByTagName("subfield")
            for field in fields:
                data = field.firstChild.data
                code = field.getAttribute("code")
                if code == 'm' and bibliosets:
                    continue
                else:
                    subfields.append((code, data))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        if date:
            record_add_field(rec, '260', subfields=[('c', date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'EDPSciences')])
        first_author = True
        for author in authors:
            if first_author:
                subfields = [('a', author[0])]
                if author[1]:
                    subfields.append(('v', author[1]))
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                subfields = [('a', author[0])]
                if author[1]:
                    subfields.append(('v', author[1]))
                record_add_field(rec, '700', subfields=subfields)
        subfields = []
        if journal and volume and first_page:
            subfields.append(('s', "%s,%s,%s" % (journal,
                                                 volume,
                                                 first_page)))
        if first_page and last_page:
            try:
                nuber_of_pages = int(last_page) - int(first_page)
                record_add_field(rec, '300', subfields=[('a', str(nuber_of_pages))])
            except ValueError:
                pass
            subfields.append(('c', '%s-%s' % (first_page,
                                              last_page)))
        if year:
            subfields.append(('y', year))
        record_add_field(rec, '773', subfields=subfields)
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        if copyright_statement:
            record_add_field(rec, '542', subfields=[('f', copyright_statement)])
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7', subfields=[('2', 'EDPSciences'),
                                                                        ('a', subject)])
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

    def get_record(self, fileName):
        """
        Gets the Marc xml of the files in xaml_jp directory

        :param fileName: the name of the file to parse.
        :type fileName: string

        :returns: a string with the marc xml version of the file.
        """
        self.doc = parse(fileName)
        rec = {}
        title = self._get_title()
        subjects = self.doc.getElementsByTagName('kwd')
        subjects = map(xml_to_text, subjects)
        subject = ', '.join(subjects)
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7', subfields=[('2', 'EDPSciences'),
                                                                        ('a', subject)])
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, volume, page, year, \
            date, doi, fpage, lpage = self._get_publication_information()
        if date:
            record_add_field(rec, '260', subfields=[('c', date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        abstract = self._get_abstract()
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'EDPSciences')])
        number_of_pages = get_attribute_in_tag(self.doc, 'page-count', 'count')
        try:
            number_of_pages = number_of_pages[0]
        except IndexError:
            pass
        if number_of_pages:
            record_add_field(rec, '300', subfields=[('a', number_of_pages)])
        emails = self._get_emails()
        authors = self._get_authors()
        affiliations = self._get_affiliations()
        first_author = True
        for author in authors:
            if first_author:
                tag = '100'
                first_author = False
            else:
                tag = '700'
            subfields = [('a', author[0])]
            if author[1]:
                affiliation = affiliations[author[1]]
                subfields.append(('v', affiliation))
            if author[2]:
                try:
                    email = emails[author[2]]
                    subfields.append(('m', email))
                except KeyError:
                    pass
            record_add_field(rec, tag, subfields=subfields)
        copyright_holder = get_value_in_tag(self.doc, 'copyright-holder')
        copyright_year = get_value_in_tag(self.doc, 'copyright-year')
        copyright_statement = get_value_in_tag(self.doc, 'copyright-statement')
        if copyright_holder and copyright_year:
            record_add_field(rec, '542', subfields=[('d', copyright_holder),
                                                    ('g', copyright_year)])
        elif copyright_statement:
            record_add_field(rec, '542', subfields=[('f', copyright_statement)])
        subfields = []
        if journal:
            subfields.append(('p', journal))
        if volume:
            subfields.append(('v', volume))
        if fpage and lpage:
            subfields.append(('c', '%s-%s' % (fpage,
                                              lpage)))
        elif page:
            subfields.append(('c', page))
        if year:
            subfields.append(('y', year))
        record_add_field(rec, '773', subfields=subfields)
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        self._add_references(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

if __name__ == '__main__':
    filename = sys.argv[1]
    edp = EDPSciencesPackage()
    if 'xml_rich' in filename:
        print(edp.get_record_rich(filename))
    else:
        print(edp.get_record(filename))
