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

from xml.dom.minidom import parse
from harvestingkit.utils import (fix_journal_name,
                                 format_arxiv_id)
from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
    record_xml_output,
)
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text,
                                         get_all_text)
from harvestingkit.jats_package import JatsPackage


class ApsPackageXMLError(Exception):

    """Raised when the XML given is of the wrong format."""


class ApsPackage(JatsPackage):

    """Parse an APS harvested file in JATS format and creating a MARCXML."""

    def __init__(self, journal_mappings=None):
        super(ApsPackage, self).__init__(journal_mappings)

    def _get_reference(self, ref):
        """Retrieve the data for a reference."""
        label = get_value_in_tag(ref, 'label')
        label = re.sub('\D', '', label)
        for innerref in ref.getElementsByTagName('mixed-citation'):
            ref_type = innerref.getAttribute('publication-type')
            institution = get_value_in_tag(innerref, 'institution')
            report_no = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'other':
                    if tag.hasChildNodes():
                        report_no = get_all_text(tag)
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
                        if author.hasChildNodes():
                            authors.append(get_all_text(author))
            editors = []
            for editor_group in person_groups:
                if editor_group.getAttribute('person-group-type') == 'editor':
                    for editor in editor_group.getElementsByTagName('string-name'):
                        if editor.hasChildNodes():
                            editors.append(get_all_text(editor))
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
                    if tag.hasChildNodes():
                        arxiv = get_all_text(tag)
            arxiv = format_arxiv_id(arxiv)
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

    def get_record(self, xml_file):
        """ Reads a xml file in JATS format and returns
            a xml string in marc format """
        self.document = parse(xml_file)

        if get_value_in_tag(self.document, "meta"):
            raise ApsPackageXMLError("The XML format of %s is not correct"
                                     % (xml_file,))
        page_count = self._get_page_count()
        rec = create_record()
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
        keywords = self._get_keywords()
        if keywords:
            record_add_field(rec, '653', ind1='1', subfields=[('a', ', '.join(keywords)),
                                                              ('9', 'author')])
        title, subtitle, _ = self._get_title()
        subfields = []
        if subtitle:
            subfields.append(('b', subtitle))
        if title:
            subfields.append(('a', title))
            record_add_field(rec, '245', subfields=subfields)
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
        license, license_type, license_url = self._get_license()
        subfields = []
        if license:
            subfields.append(('a', license))
        if license_url:
            subfields.append(('u', license_url))
        if subfields:
            record_add_field(rec, '540', subfields=subfields)
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
