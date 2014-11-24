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
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.utils import (collapse_initials,
                                 fix_title_capitalization,
                                 record_add_field,
                                 create_record,
                                 record_xml_output,
                                 fix_name_capitalization)
from xml.dom.minidom import parse
from harvestingkit.jats_package import JatsPackage


class WorldScientific(JatsPackage):
    """
    This class is specialized in parsing files from EdpSciences FTP server
    and converting them in Marc XML.
    """
    def __init__(self, journal_mappings={}):
        super(WorldScientific, self).__init__(journal_mappings)

    def _get_date(self):
        for date in self.document.getElementsByTagName('date'):
            if date.getAttribute('date-type') == 'published':
                year = get_value_in_tag(date, 'year')
                month = get_value_in_tag(date, 'month').zfill(2)
                day = get_value_in_tag(date, 'day').zfill(2)
                return '%s-%s-%s' % (year, month, day)
        for date in self.document.getElementsByTagName('pub-date'):
            if date.getAttribute('pub-type') == 'ppub':
                month = get_value_in_tag(date, 'month').zfill(2)
                year = get_value_in_tag(date, 'year')
                day = '01'
                return '%s-%s-%s' % (year, month, day)
        for date in self.document.getElementsByTagName('pub-date'):
            if date.getAttribute('pub-type') == 'epub':
                month = get_value_in_tag(date, 'month').zfill(2)
                year = get_value_in_tag(date, 'year')
                day = '01'
                return '%s-%s-%s' % (year, month, day)

    def get_date(self, filename):
        self.document = parse(filename)
        return self._get_date()

    def _get_authors(self):
        authors = []
        for contrib in self.document.getElementsByTagName('contrib'):
            if contrib.getAttribute('contrib-type') == 'author':
                surname = get_value_in_tag(contrib, 'surname')
                given_names = get_value_in_tag(contrib, 'given-names')
                given_names = collapse_initials(given_names)
                surname, given_names = fix_name_capitalization(
                    surname, given_names.split()
                )
                name = '%s, %s' % (surname, given_names)
                affiliations = []
                for aff in contrib.getElementsByTagName('aff'):
                    affiliations.append(xml_to_text(aff))
                emails = []
                for email in contrib.getElementsByTagName('email'):
                    emails.append(xml_to_text(email))
                authors.append((name, affiliations, emails))
        return authors

    def _add_authors(self, rec):
        authors = self._get_authors()
        first_author = True
        for author in authors:
            subfields = [('a', author[0])]
            if author[1]:
                for aff in author[1]:
                    subfields.append(('v', aff))
            if author[2]:
                for email in author[2]:
                    subfields.append(('m', email))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)

    def get_record(self, fileName, ref_extract_callback=None):
        """
        Gets the Marc xml of the files in xaml_jp directory

        :param fileName: the name of the file to parse.
        :type fileName: string
        :param refextract_callback: callback to be used to extract
                                    unstructured references. It should
                                    return a marcxml formated string
                                    of the reference.
        :type refextract_callback: callable

        :returns: a string with the marc xml version of the file.
        """
        self.document = parse(fileName)
        article_type = self._get_article_type()
        if article_type not in ['research-article',
                                'introduction',
                                'letter',
                                'correction']:
            return ''
        rec = create_record()
        title, subtitle, notes = self._get_title()
        subfields = []
        if subtitle:
            subfields.append(('b', subtitle))
        if title:
            title = fix_title_capitalization(title)
            subfields.append(('a', title))
            record_add_field(rec, '245', subfields=subfields)
        subjects = self.document.getElementsByTagName('kwd')
        subjects = map(xml_to_text, subjects)
        for note_id in notes:
            note = self._get_note(note_id)
            if note:
                record_add_field(rec, '500', subfields=[('a', note)])
        for subject in subjects:
            record_add_field(rec, '650', ind1='1', ind2='7',
                             subfields=[('2', 'World Scientific'),
                                        ('a', subject)])
        keywords = self._get_keywords()
        for keyword in keywords:
            record_add_field(rec, '653', ind1='1', subfields=[('a', keyword),
                                                              ('9', 'author')])
        journal, volume, issue, year, date, doi, page,\
            fpage, lpage = self._get_publication_information()
        if date:
            record_add_field(rec, '260', subfields=[('c', date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        abstract = self._get_abstract()
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'World Scientific')])
        license, license_type, license_url = self._get_license()
        subfields = []
        if license:
            subfields.append(('a', license))
        if license_url:
            subfields.append(('u', license_url))
        if subfields:
            record_add_field(rec, '540', subfields=subfields)
        if license_type == 'open-access':
            self._attach_fulltext(rec, doi)
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
        if issue:
            subfields.append(('n', issue))
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
        conference = ''
        for tag in self.document.getElementsByTagName('conference'):
            conference = xml_to_text(tag)
        if conference:
            record_add_field(rec, '980', subfields=[('a', 'ConferencePaper')])
            record_add_field(rec, '500', subfields=[('a', conference)])
        self._add_authors(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""


if __name__ == '__main__':
    filename = sys.argv[1]
    ws = WorldScientific()
    print(ws.get_record(filename))
