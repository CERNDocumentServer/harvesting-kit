# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014, 2016 CERN.
#
# Harvesting Kit is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Harvesting Kit is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import sys

from datetime import datetime

from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.utils import collapse_initials, safe_title
from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
)


class PosPackage(object):
    """ This class is specialized in parsing xml records from
    PoS and create the corresponding Bibrecord object. """

    def _get_authors(self):
        authors = []
        for pextag in self.document.getElementsByTagName('pex-dc:creator'):
            affiliations = []
            for auttag in pextag.getElementsByTagName('pex-dc:name'):
                author = xml_to_text(auttag)
                lastname = author.split()[-1]
                givenames = " ".join(author.split()[:-1])
                givenames = collapse_initials(givenames)
                name = "%s, %s" % (lastname, givenames)
                name = safe_title(name)
                for afftag in pextag.getElementsByTagName('pex-dc:affiliation'):
                    if afftag:
                        affiliations.append(xml_to_text(afftag))
                authors.append((name, affiliations))
        return authors

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'pex-dc:title')
        except Exception:
            print >> sys.stderr, "Can't find title"
            return ''

    def _get_language(self):
        try:
            return get_value_in_tag(self.document, 'pex-dc:language')
        except Exception:
            print >> sys.stderr, "Can't find language"
            return ''

    def _get_publisher(self):
        try:
            publisher = get_value_in_tag(self.document, 'pex-dc:publisher')
            if publisher == 'Sissa Medialab':
                publisher = 'SISSA'
            return publisher
        except Exception:
            print >> sys.stderr, "Can't find publisher"
            return ''

    def _get_date(self):
        try:
            date = get_value_in_tag(self.document, 'pex-dc:date')
            if len(date) == 20:
                date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
                date = date.strftime("%Y-%m-%d")
                date = str(date)
            return date
        except Exception:
            print >> sys.stderr, "Can't find date"
            return ''

    def _get_copyright(self):
        try:
            record_copyright = get_value_in_tag(self.document, 'pex-dc:rights')
            if record_copyright == 'Creative Commons Attribution-NonCommercial-ShareAlike':
                record_copyright = 'CC-BY-NC-SA'
            return record_copyright
        except Exception:
            print >> sys.stderr, "Can't find copyright"
            return ''

    def _get_subject(self):
        try:
            return get_value_in_tag(self.document, 'pex-dc:subject')
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

    def get_record(self, record):
        """ Reads a dom xml element in oaidc format and
            returns the bibrecord object """
        self.document = record
        rec = create_record()
        language = self._get_language()
        if language and language != 'en':
            record_add_field(rec, '041', subfields=[('a', language)])
        publisher = self._get_publisher()
        date = self._get_date()
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
        record_copyright = self._get_copyright()
        if record_copyright:
            record_add_field(rec, '540', subfields=[('a', record_copyright)])
        subject = self._get_subject()
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7', subfields=[('a', subject),
                                                                        ('2', 'PoS')])
        authors = self._get_authors()
        first_author = True
        for author in authors:
            subfields = [('a', author[0])]
            for affiliation in author[1]:
                subfields.append(('v', affiliation))
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
