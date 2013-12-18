# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Add the timestamp from CrossRef
"""

from invenio.crossrefutils import get_registration_timestamp_for_dois

def check_records(records):
    """
    Amend the records to add the DOI registration timestamp.
    """
    doi_to_record = {}
    for record in records:
        doi_found = False
        doi_timestamp_found = False
        for position, value in record.iterfield('0247_t'):
            doi_timestamp_found = True
            break
        else:
            for position, value in record.iterfield('0247_a'):
                if value.startswith('10.'):
                    if doi_found:
                        record.set_invalid("More than one DOI found")
                        break
                    if value in doi_to_record:
                        record.set_invalid("Found DOI %s that was already associated with a previous record!" % value)
                        break
                    doi_to_record[value] = (record, position)
                    doi_found = True
        if doi_timestamp_found:
            continue
    doi_to_timestamp = get_registration_timestamp_for_dois(doi_to_record.keys())
    for doi, (record, position) in doi_to_record.iteritems():
        if doi_to_timestamp.get(doi):
            timestamp = doi_to_timestamp[doi]
            record.add_subfield(position, 't', timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'))
        else:
            record.warn("%s is not (yet) registered in CrossRef" % doi)



