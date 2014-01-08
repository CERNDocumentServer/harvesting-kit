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
    '1475-7516': 'J. Cosmol. Astropart. Phys.',
    '1367-2630': 'New J. Phys.',
    '1674-1137': 'Chinese Phys. C',
}

def check_records(records):
    """
    Amend the records to rename 773__p from issn to journal name
    """
    for record in records:
        for position, value in record.iterfield('773__p'):
            if value in CFG_ISSN_MAP:
                record.amend_field(position, CFG_ISSN_MAP[value])

