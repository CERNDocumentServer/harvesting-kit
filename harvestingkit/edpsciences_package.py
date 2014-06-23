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
            return get_value_in_tag(self.document, 'abstract')
        except Exception:
            print("Can't find abstract", file=sys.stderr)
            return ''

    def _get_journal(self):
        try:
            title = get_value_in_tag(self.document, 'abbrev-journal-title')
            if not title:
                title = get_value_in_tag(self.document, 'journal-title')
            try:
                title = self.journal_mappings[title.upper()]
            except KeyError:
                pass
            title = title.replace('. ', '.')
            return title.strip()
        except Exception:
            print("Can't find journal-title", file=sys.stderr)
            return ''

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'publisher')
        except Exception:
            print("Can't find publisher", file=sys.stderr)
            return ''

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'article-title')
        except Exception:
            print("Can't find title", file=sys.stderr)
            return ''

    def _get_date(self):
        final = ''
        epub_date = ''
        ppub_date = ''
        for dateTag in self.document.getElementsByTagName('pub-date'):
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
                    epub_date = dateTag.getAttribute('iso-8601-date')
            elif dateTag.getAttribute('pub-type') == 'ppub':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    ppub_date = str(date(year, month, day))
                except ValueError:
                    ppub_date = dateTag.getAttribute('iso-8601-date')
        if final:
            return final
        elif epub_date:
            return epub_date
        elif ppub_date:
            return ppub_date
        else:
            print("Can't find publication date", file=sys.stderr)
            return datetime.now().strftime("%Y-%m-%d")

    def _get_doi(self):
        try:
            for tag in self.document.getElementsByTagName('article-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    return tag.firstChild.data
        except Exception:
            print("Can't find doi", file=sys.stderr)
            return ''

    def _get_page_count(self):
        try:
            return get_attribute_in_tag(self.document, 'page-count', 'count')[0]
        except IndexError:
            print("Can't find page count", file=sys.stderr)
            return ''

    def _get_license(self):
        license = ''
        license_type = ''
        for tag in self.document.getElementsByTagName('license'):
            license = get_value_in_tag(tag, 'ext-link')
            license_type = tag.getAttribute('license-type')
        return license, license_type

    def _get_authors(self):
        authors = []
        for contrib in self.document.getElementsByTagName('contrib'):
            if contrib.getAttribute('contrib-type') == 'author':
                surname = get_value_in_tag(contrib, 'surname')
                given_names = get_value_in_tag(contrib, 'given-names')
                given_names = collapse_initials(given_names)
                name = '%s, %s' % (surname, given_names)
                affiliations = []
                corresp = ''
                for tag in contrib.getElementsByTagName('xref'):
                    if tag.getAttribute('ref-type') == 'aff':
                        affiliations.extend(tag.getAttribute('rid').split())
                    elif tag.getAttribute('ref-type') == 'corresp' or\
                            tag.getAttribute('ref-type') == 'author-notes':
                        corresp = tag.getAttribute('rid')
                authors.append((name, affiliations, corresp))
        return authors

    def _get_pacscodes(self):
        pacscodes = []
        for tag in self.document.getElementsByTagName('kwd-group'):
            if tag.getAttribute('kwd-group-type') == 'pacs':
                for code in tag.getElementsByTagName('kwd'):
                    pacscodes.append(xml_to_text(code))
        return pacscodes

    def _get_copyright(self):
        try:
            copyright_holder = get_value_in_tag(self.document, 'copyright-holder')
            copyright_year = get_value_in_tag(self.document, 'copyright-year')
            copyright_statement = get_value_in_tag(self.document, 'copyright-statement')
            return copyright_holder, copyright_year, copyright_statement
        except Exception:
            print("Can't find copyright", file=sys.stderr)
            return '', '', ''

    def _get_publication_information(self):
        journal = self._get_journal()
        date = self._get_date()
        doi = self._get_doi()
        issue = get_value_in_tag(self.document, 'issue')
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        volume += get_value_in_tag(self.document, 'volume')
        page = get_value_in_tag(self.document, 'elocation-id')
        fpage = get_value_in_tag(self.document, 'fpage')
        lpage = get_value_in_tag(self.document, 'lpage')
        year = date[:4]
        return (journal, volume, issue, year, date, doi, page, fpage, lpage)

    def _get_affiliations(self):
        affiliations = {}
        for tag in self.document.getElementsByTagName('aff'):
            aid = tag.getAttribute('id')
            affiliation = xml_to_text(tag)
            #removes the label
            try:
                int(affiliation.split()[0])
                affiliation = ' '.join(affiliation.split()[1:])
            except ValueError:
                pass
            affiliations[aid] = affiliation
        return affiliations

    def _get_author_emails(self):
        author_emails = {}
        for tag in self.document.getElementsByTagName('author-notes'):
            email_elements = tag.getElementsByTagName('corresp')
            email_elements += tag.getElementsByTagName('fn')
            for tg in email_elements:
                nid = tg.getAttribute('id')
                email = xml_to_text(tg)
                email = email.replace(';', '')
                #removes the label
                if email.split() > 1:
                    emails = email.split()[1:]
                valid_emails = []
                for email in emails:
                    if '@' in email and '.' in email:
                        valid_emails.append(email)
                author_emails[nid] = valid_emails
        return author_emails

    def _get_subject(self):
        subjects = []
        for tag in self.document.getElementsByTagName('subj-group'):
            if tag.getAttribute('subj-group-type') == 'toc-minor':
                for subject in tag.getElementsByTagName('subject'):
                    subjects.append(xml_to_text(subject))
        return ', '.join(subjects)

    def _add_authors(self, rec):
        authors = self._get_authors()
        affiliations = self._get_affiliations()
        author_emails = self._get_author_emails()
        first_author = True
        for author in authors:
            subfields = [('a', author[0])]
            if author[1]:
                for aff in author[1]:
                    subfields.append(('v', affiliations[aff]))
            if author[2]:
                for email in author_emails[author[2]]:
                    subfields.append(('m', email))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)

    def _get_references(self):
        for ref in self.document.getElementsByTagName('ref'):
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
            if ref_type == 'journal':
                source, vol = fix_journal_name(source, self.journal_mappings)
                if vol:
                    volume = vol + volume
            yield ref_type, text_ref, ext_link, authors, year, source, volume, page

    def _add_references(self, rec):
        for ref_type, text_ref, ext_link, authors, year, \
                source, volume, page in self._get_references():
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
        self.document = parse(filename)
        rec = {}
        articles = self.document.getElementsByTagName('ArticleID')
        for article in articles:
            article_type = article.getAttribute('Type')
            if not article_type == 'Article':
                return ''
            doi = get_value_in_tag(self.document, 'DOI')
            date = ''
            for tag in self.document.getElementsByTagName('Accepted'):
                year = get_value_in_tag(tag, 'Year')
                month = get_value_in_tag(tag, 'Month').zfill(2)
                day = get_value_in_tag(tag, 'Day').zfill(2)
                date = "%s-%s-%s" % (year, month, day)
            if not date:
                for tag in self.document.getElementsByTagName('OnlineDate'):
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
        journal = get_value_in_tag(self.document, 'JournalTitle')
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        issues = self.document.getElementsByTagName('IssueID')
        for issue in issues:
            volume += get_value_in_tag(issue, 'Volume')
            year = get_value_in_tag(issue, 'Year')
        title = get_value_in_tag(self.document, 'Title')
        authors = self.document.getElementsByTagName('Author')
        affiliations = self.document.getElementsByTagName('Affiliation')

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
        abstract = get_value_in_tag(self.document, 'Abstract')
        references = self.document.getElementsByTagName('Bibliomixed')

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
        self.document = parse(fileName)
        rec = {}
        title = self._get_title()
        subjects = self.document.getElementsByTagName('kwd')
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
        number_of_pages = self._get_page_count()
        if number_of_pages:
            record_add_field(rec, '300', subfields=[('a', number_of_pages)])
        c_holder, c_year, c_statement = self._get_copyright()
        if c_holder and c_year:
            record_add_field(rec, '542', subfields=[('d', c_holder),
                                                    ('g', c_year),
                                                    ('e', 'Article')])
        elif c_statement:
            record_add_field(rec, '542', subfields=[('f', c_statement),
                                                    ('e', 'Article')])
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
        self._add_authors(rec)
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
