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
import re

from invenio.refextract_kbs import get_kbs
from datetime import datetime
from xml.dom.minidom import parse
from harvestingkit.utils import (fix_journal_name,
                                 collapse_initials,
                                 format_arxiv_id)
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text,
                                         get_attribute_in_tag)
from invenio.bibrecord import (record_add_field,
                               record_xml_output)
from datetime import date


class ApsPackageXMLError(Exception):
    """ Raised when the XML given is of the wrong format """
    pass


class ApsPackage(object):
    """
    This class is specialized in parsing an APS harvested file in JATS format
    and creating a Inspire-compatible bibupload containing the original
    XML and every possible metadata filled in.
    """
    def __init__(self, journal_mappings=None):
        if journal_mappings:
            self.journal_mappings = journal_mappings
        else:
            try:
                self.journal_mappings = get_kbs()['journals'][1]
            except KeyError:
                self.journal_mappings = {}

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

    def _get_abstract(self):
        try:
            return get_value_in_tag(self.document, 'abstract')
        except Exception:
            print("Can't find abstract", file=sys.stderr)
            return ''

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'article-title')
        except Exception:
            print("Can't find title", file=sys.stderr)
            return ''

    def _get_doi(self):
        try:
            for tag in self.document.getElementsByTagName('article-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    return tag.firstChild.data
        except Exception:
            print("Can't find doi", file=sys.stderr)
            return ''

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
            for note in tag.getElementsByTagName('fn'):
                nid = note.getAttribute('id')
                email = xml_to_text(note)
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

    def _get_license(self):
        license = ''
        license_type = ''
        for tag in self.document.getElementsByTagName('license'):
            license = get_value_in_tag(tag, 'ext-link')
            license_type = tag.getAttribute('license-type')
        return license, license_type

    def _get_page_count(self):
        try:
            return get_attribute_in_tag(self.document, 'page-count', 'count')[0]
        except IndexError:
            print("Can't find page count", file=sys.stderr)
            return ''

    def _get_copyright(self):
        try:
            copyright_holder = get_value_in_tag(self.document, 'copyright-holder')
            copyright_year = get_value_in_tag(self.document, 'copyright-year')
            copyright_statement = get_value_in_tag(self.document, 'copyright-statement')
            return copyright_holder, copyright_year, copyright_statement
        except Exception:
            print("Can't find copyright", file=sys.stderr)
            return '', '', ''

    def _get_pacscodes(self):
        pacscodes = []
        for tag in self.document.getElementsByTagName('kwd-group'):
            if tag.getAttribute('kwd-group-type') == 'pacs':
                for code in tag.getElementsByTagName('kwd'):
                    pacscodes.append(xml_to_text(code))
        return pacscodes

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

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'publisher')
        except Exception:
            print("Can't find publisher", file=sys.stderr)
            return ''

    def _get_subject(self):
        subjects = []
        for tag in self.document.getElementsByTagName('subj-group'):
            if tag.getAttribute('subj-group-type') == 'toc-minor':
                for subject in tag.getElementsByTagName('subject'):
                    subjects.append(xml_to_text(subject))
        return ', '.join(subjects)

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

    def _get_reference(self, ref):
        """ Retrieves the data for a reference """
        label = get_value_in_tag(ref, 'label')
        label = re.sub('\D', '', label)
        for innerref in ref.getElementsByTagName('mixed-citation'):
            ref_type = innerref.getAttribute('publication-type')
            institution = get_value_in_tag(innerref, 'institution')
            report_no = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'other':
                    report_no = tag.firstChild.data
            doi = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    doi = xml_to_text(tag)
            collaboration = get_value_in_tag(innerref, 'collab')
            authors = []
            person_groups = innerref.getElementsByTagName('person-group')
            for author_group in person_groups:
                if author_group.getAttribute('person-group-type') == 'author':
                    for author in author_group.getElementsByTagName('string-name'):
                        try:
                            authors.append(author.firstChild.data)
                        except AttributeError:
                            pass
            editors = []
            for editor_group in person_groups:
                if editor_group.getAttribute('person-group-type') == 'editor':
                    for editor in editor_group.getElementsByTagName('string-name'):
                        try:
                            editors.append(editor.firstChild.data)
                        except AttributeError:
                            pass
            journal = get_value_in_tag(innerref, 'source')
            journal, volume = fix_journal_name(journal, self.journal_mappings)
            volume += get_value_in_tag(innerref, 'volume')
            if journal == 'J.High Energy Phys.' or journal == 'JHEP':
                issue = get_value_in_tag(innerref, 'issue')
                volume = volume[2:] + issue
                journal = 'JHEP'
            page = get_value_in_tag(innerref, 'page-range')
            year = get_value_in_tag(innerref, 'year')
            external_link = get_value_in_tag(innerref, 'ext-link')
            arxiv = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'arxiv':
                    arxiv = tag.firstChild.data
            arxiv = format_arxiv_id(arxiv, True)
            publisher = get_value_in_tag(innerref, 'publisher-name')
            publisher_location = get_value_in_tag(innerref, 'publisher-loc')
            if publisher_location:
                publisher = publisher_location + ': ' + publisher
            unstructured_text = []
            for child in innerref.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    text = child.nodeValue.strip()
                    text = re.sub(r'[\[\]\(\.;\)]', '', text).strip()
                    if text.startswith(','):
                        text = text[1:].strip()
                    if text.endswith('Report No'):
                        text = institution + " " + text
                        institution = ''
                        text = text.strip()
                    elif text.endswith(' ed'):
                        text += '.'
                    elif text.endswith('PhD thesis,'):
                        if institution:
                            text += ' ' + institution
                            institution = ''
                        else:
                            text = text[:-1]
                    elif text.startswith('Seminar,'):
                        article_title = get_value_in_tag(innerref, 'article-title')
                        text = institution + " Seminar, \"" + article_title + "\""
                        institution = ''
                    elif text == u'\u201d':
                        text = ''
                    ignore_text = ['in', 'pp', 'edited by']
                    if text.startswith('Vol'):
                        temp = re.sub(r'\D', '', text)
                        if temp:
                            volume += temp
                    elif len(text) > 1 and text not in ignore_text\
                            and not (text.isdigit() or text[:-1].isdigit()):
                        unstructured_text.append(text)
            if unstructured_text:
                unstructured_text = " ".join(unstructured_text)
            if ref_type == 'book':
                if volume and not volume.lower().startswith('vol'):
                    volume = 'Vol ' + volume
                if volume and page:
                    volume = volume + ', pp ' + page
            yield ref_type, doi, authors, collaboration, journal, volume, page, year,\
                label, arxiv, publisher, institution, unstructured_text, external_link,\
                report_no, editors

    def _add_references(self, rec):
        """ Adds the reference to the record """
        for ref in self.document.getElementsByTagName('ref'):
            for ref_type, doi, authors, collaboration, journal, volume, page, year,\
                    label, arxiv, publisher, institution, unstructured_text,\
                    external_link, report_no, editors in self._get_reference(ref):
                subfields = []
                if doi:
                    subfields.append(('a', doi))
                for author in authors:
                    subfields.append(('h', author))
                for editor in editors:
                    subfields.append(('e', editor))
                if year:
                    subfields.append(('y', year))
                if unstructured_text:
                    if page:
                        subfields.append(('m', unstructured_text + ', ' + page))
                    else:
                        subfields.append(('m', unstructured_text))
                if collaboration:
                    subfields.append(('c', collaboration))
                if institution:
                    subfields.append(('m', institution))
                if publisher:
                    subfields.append(('p', publisher))
                if arxiv:
                    subfields.append(('r', arxiv))
                if report_no:
                    subfields.append(('r', report_no))
                if external_link:
                    subfields.append(('u', external_link))
                if label:
                    subfields.append(('o', label))
                if ref_type == 'book':
                    if journal:
                        subfields.append(('t', journal))
                    if volume:
                        subfields.append(('m', volume))
                    elif page and not unstructured_text:
                        subfields.append(('m', page))
                else:
                    if volume and page:
                        subfields.append(('s', journal + "," + volume + "," + page))
                    elif journal:
                        subfields.append(('t', journal))
                if ref_type:
                    subfields.append(('d', ref_type))
                if not subfields:
                    #misc-type references
                    try:
                        r = ref.getElementsByTagName('mixed-citation')[0]
                        text = xml_to_text(r)
                        label = text.split()[0]
                        text = " ".join(text.split()[1:])
                        subfields.append(('s', text))
                        record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                    except IndexError:
                        #references without 'mixed-citation' tag
                        try:
                            r = ref.getElementsByTagName('note')[0]
                            subfields.append(('s', xml_to_text(r)))
                            record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                        except IndexError:
                            #references without 'note' tag
                            subfields.append(('s', xml_to_text(ref)))
                            record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                else:
                    record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

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

    def get_record(self, xml_file):
        """ Reads a xml file in JATS format and returns
            a xml string in marc format """
        self.document = parse(xml_file)

        if get_value_in_tag(self.document, "meta"):
            raise ApsPackageXMLError("The XML format of %s is not correct"
                                     % (xml_file,))
        rec = {}
        page_count = self._get_page_count()
        if page_count:
            record_add_field(rec, '300', subfields=[('a', page_count)])
        pacscodes = self._get_pacscodes()
        for pacscode in pacscodes:
            record_add_field(rec, '084', subfields=[('2', 'PACS'),
                                                    ('a', pacscode)])
        subject = self._get_subject()
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7', subfields=[('2', 'APS'),
                                                                        ('a', subject)])
        title = self._get_title()
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, volume, issue, year, start_date, doi,\
            article_id, _, _ = self._get_publication_information()
        if start_date:
            record_add_field(rec, '260', subfields=[('c', start_date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        abstract = self._get_abstract()
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'APS')])
        c_holder, c_year, c_statement = self._get_copyright()
        c_holder, c_year, c_statement = self._get_copyright()
        if c_holder and c_year:
            record_add_field(rec, '542', subfields=[('d', c_holder),
                                                    ('g', c_year),
                                                    ('e', 'Article')])
        elif c_statement:
            record_add_field(rec, '542', subfields=[('f', c_statement),
                                                    ('e', 'Article')])
        record_add_field(rec, '773', subfields=[('p', journal),
                                                ('v', volume),
                                                ('n', issue),
                                                ('y', year),
                                                ('c', article_id)])
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        record_add_field(rec, '980', subfields=[('a', 'Citeable')])
        record_add_field(rec, '980', subfields=[('a', 'Published')])
        self._add_authors(rec)
        self._add_references(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            sys.stderr.write("""Found a bad char in the file
                                for the article """ + doi)
            return ""


def main(args):
    if len(args) != 1:
        print("usage: python aps_package.py <filename>")
        sys.exit()
    a = ApsPackage()
    print(a.get_record(args[0]))

if __name__ == '__main__':
    main(sys.argv[1:])
