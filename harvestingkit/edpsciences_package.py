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
import sys
import os
import tarfile
import re
from invenio.refextract_kbs import get_kbs
from harvestingkit.ftp_utils import FtpDownloader
from invenio.bibrecord import record_add_field, record_xml_output
from harvestingkit.minidom_utils import get_value_in_tag, xml_to_text
from harvestingkit.utils import collapse_initials, fix_journal_name
from xml.dom.minidom import parse
from datetime import date, datetime


class EDPSciencesPackage(object):

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
        for title in self.doc.getElementsByTagName('title-group'):
            return xml_to_text(title)

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
        for article_id in self.doc.getElementsByTagName('article_id'):
            if article_id.getAttribute('pub-id-type') == 'doi':
                return article_id.firstChild.data

    def _get_authors(self):
        authors = []
        for contrib in self.doc.getElementsByTagName('contrib'):
            if contrib.getAttribute('contrib-type') == 'author':
                surname = get_value_in_tag(contrib, 'surname')
                given_names = get_value_in_tag(contrib, 'given-names')
                given_names = collapse_initials(given_names)
                name = '%s, %s' % (surname, given_names)
                affiliation = ''
                for aff in contrib.getElementsByTagName('xref'):
                    if aff.getAttribute('ref-type') == 'aff':
                        affiliation = aff.getAttribute('rid')
                authors.append((name, affiliation))
        return authors

    def _get_publication_information(self):
        journal = self._get_journal_name()
        date = self._get_date()
        doi = self._get_doi()
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        volume += get_value_in_tag(self.doc, 'volume')
        issue = get_value_in_tag(self.doc, 'elocation-id')
        year = date[:4]
        return (journal, volume, issue, year, date, doi)

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

    def get_record(self, fileName):
        self.doc = parse(fileName)
        rec = {}
        title = self._get_title()
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, volume, issue, year, date, doi = self._get_publication_information()
        if date:
            record_add_field(rec, '260', subfields=[('c', date)])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        abstract = self._get_abstract()
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'EDPSciences')])
        authors = self._get_authors()
        affiliations = self._get_affiliations()
        first_author = True
        for author in authors:
            if first_author:
                subfields = [('a', author[0])]
                if author[1]:
                    affiliation = affiliations[author[1]]
                    subfields.append(('v', affiliation))
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                subfields = [('a', author[0])]
                if author[1]:
                    affiliation = affiliations[author[1]]
                    subfields.append(('v', affiliation))
                record_add_field(rec, '700', subfields=subfields)
        copyright_holder = get_value_in_tag(self.doc, 'copyright-holder')
        copyright_year = get_value_in_tag(self.doc, 'copyright-year')
        copyright_statement = get_value_in_tag(self.doc, 'copyright-statement')
        if copyright_holder and copyright_year:
            record_add_field(rec, '542', subfields=[('d', copyright_holder),
                                                    ('g', copyright_year)])
        elif copyright_statement:
            record_add_field(rec, '542', subfields=[('f', copyright_statement)])
        record_add_field(rec, '773', subfields=[('p', journal),
                                                ('v', volume),
                                                ('n', issue),
                                                ('y', year)])
        self._add_references(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""
