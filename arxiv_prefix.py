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
Correct missing arxiv: prefix
"""

import re

RE_NO_PREFIX = re.compile(r"\d+\.\d+")

def check_records(records):
    """
    Correct missing arxiv: prefix
    """
    for record in records:
        for position, value in record.iterfield('037__a'):
            if RE_NO_PREFIX.match(value):
                record.amend_field(position, 'arXiv:' + value)
