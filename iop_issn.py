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
Correct IOP ISSN into actual journal names
"""

CFG_ISSN_MAP = {
    '1475-7516': 'JCAP',
    '1367-2630': 'New J. Phys.',
    '1674-1137': 'Chinese Phys. C',
}

def check_records(records):
    """
    Amend the records to rename 773__p from issn to journal name
    """
    for record in records:
        jcap_article = False
        for position, value in record.iterfield('773__p'):
            if value in ('1475-7516', 'JCAP'):
                jcap_article = True
            if value in CFG_ISSN_MAP:
                record.amend_field(position, CFG_ISSN_MAP[value])

        if jcap_article:
            ## JCAP volumes should be changed from the full year to:
            ## last two year digits followed by issue number (to follow INSPIRE
            ## convention)
            tag_773 = dict([(position[0][5], (position, value)) for position, value in record.iterfield('773__%')])
            if tag_773['v'][1].startswith('20'):
                position = tag_773['v'][0]
                new_value = tag_773['v'][1][2:] + tag_773['n'][1]
                record.amend_field(position, new_value)


