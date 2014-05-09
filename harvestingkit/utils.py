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
import re


def collapse_initials(name):
    """ Removes the space between initials.
        eg T. A. --> T.A."""
    if len(name.split()) > 1:
        name = re.sub(r'([A-Z]\.) (?=[A-Z]\.)', r'\1', name)
    return name


def fix_journal_name(journal, knowledge_base):
    """ Converts journal name to Inspire's short form """
    if not journal:
        return '', ''
    volume = ''
    if (journal[-1] <= 'Z' and journal[-1] >= 'A') \
            and (journal[-2] == '.' or journal[-2] == ' '):
        volume += journal[-1]
        journal = journal[:-1]
    try:
        journal = knowledge_base[journal.upper()].strip()
    except KeyError:
        try:
            journal = knowledge_base[journal].strip()
        except KeyError:
            pass
    journal = journal.replace('. ', '.')
    return journal, volume
