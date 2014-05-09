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
from datetime import datetime

from harvestingkit.minidom_utils import get_value_in_tag, xml_to_text
from invenio.bibrecord import record_add_field
from harvestingkit.utils import collapse_initials


class PosPackage(object):
    """ This class is specialized in parsing xml records from
    PoS and create the corresponding Bibrecord object. """

    def _get_doi(self):
        try:
            for tag in self.document.getElementsByTagName('article-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    return tag.firstChild.data
        except Exception:
            print >> sys.stderr, "Can't find doi"
            return ''

    def _get_authors(self):
        authors = []
        for tag in self.document.getElementsByTagName('dc:creator'):
            author = xml_to_text(tag)
            lastname = author.split()[-1]
            lastname = lastname[0] + lastname[1:].lower()
            givennames = ''
            for name in author.split()[:-1]:
                name = name[0] + name[1:].lower()
                givennames += name + ' '
            givennames = collapse_initials(givennames.strip())
            authors.append("%s, %s" % (lastname, givennames))
        return authors

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'dc:title')
        except Exception:
            print >> sys.stderr, "Can't find title"
            return ''

    def _ge_language(self):
        try:
            return get_value_in_tag(self.document, 'dc:language')
        except Exception:
            print >> sys.stderr, "Can't find language"
            return ''

    def _get_description(self):
        try:
            return get_value_in_tag(self.document, 'dc:description')
        except Exception:
            print >> sys.stderr, "Can't find description"
            return ''

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'dc:publisher')
        except Exception:
            print >> sys.stderr, "Can't find publisher"
            return ''

    def _get_date(self):
        try:
            return get_value_in_tag(self.document, 'dc:date')
        except Exception:
            print >> sys.stderr, "Can't find date"
            return ''

    def _get_copyright(self):
        try:
            return get_value_in_tag(self.document, 'dc:rights')
        except Exception:
            print >> sys.stderr, "Can't find copyright"
            return ''

    def _get_subject(self):
        try:
            return get_value_in_tag(self.document, 'dc:subject')
        except Exception:
            print >> sys.stderr, "Can't find subject"
            return ''

    def get_identifier(self):
        """ Returns the identifier of the paper corresponding
            to this record containing the conference which it
            was published and the proceeding number."""
        try:
            return get_value_in_tag(self.document, 'identifier')
        except Exception:
            print >> sys.stderr, "Can't find identifier"
            return ''

    def _get_datestamp(self):
        try:
            return get_value_in_tag(self.document, 'datestamp')
        except Exception:
            print >> sys.stderr, "Can't find datestamp"
            return ''

    def get_record(self, record):
        """ Reads a dom xml element in oaidc format and
            returns the bibrecord object """
        self.document = record
        rec = {}
        language = self._ge_language()
        if language and language != 'en':
            record_add_field(rec, '041', subfields=[('a', language)])
        description = self._get_description()
        if description:
            record_add_field(rec, '500', subfields=[('a', description)])
        publisher = self._get_publisher()
        if publisher == 'Sissa Medialab':
            publisher = 'SISSA'
        date = self._get_date()
        if len(date) == 20:
            date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
            date = date.strftime("%Y-%m-%d")
            date = str(date)
        if publisher and date:
            record_add_field(rec, '260', subfields=[('b', publisher),
                                                    ('c', date)])
        elif publisher:
            record_add_field(rec, '260', subfields=[('b', publisher)])
        elif date:
            record_add_field(rec, '260', subfields=[('c', date)])
        title = self._get_title()
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        copyrightt = self._get_copyright()
        if copyrightt == 'Creative Commons Attribution-NonCommercial-ShareAlike':
            copyrightt = 'CC-BY-NC-SA'
        if copyrightt:
            record_add_field(rec, '540', subfields=[('a', copyrightt)])
        subject = self._get_subject()
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7', subfields=[('a', subject)])
        authors = self._get_authors()
        first_author = True
        for author in authors:
            subfields = [('a', author)]
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        identifier = self.get_identifier()
        conference = identifier.split(':')[2]
        conference = conference.split('/')[0]
        contribution = identifier.split(':')[2]
        contribution = contribution.split('/')[1]
        record_add_field(rec, '773', subfields=[('p', 'PoS'),
                                                ('v', conference.replace(' ', '')),
                                                ('c', contribution),
                                                ('y', date[:4])])
        record_add_field(rec, '980', subfields=[('a', 'ConferencePaper')])
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        return rec
