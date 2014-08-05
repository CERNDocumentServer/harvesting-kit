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
from xml.dom.minidom import Document, parseString


def create_record():
    doc = Document()
    record = doc.createElement('record')
    return record


def record_add_field(rec, tag, ind1='', ind2='', subfields=[], controlfield_value=''):
    doc = Document()
    datafield = doc.createElement('datafield')
    datafield.setAttribute('tag', tag)
    datafield.setAttribute('ind1', ind1)
    datafield.setAttribute('ind2', ind2)
    for subfield in subfields:
        field = doc.createElement('subfield')
        field.setAttribute('code', subfield[0])
        ## In order to be parsed it needs to a propper XML
        data = "<dummy>" + escape_for_xml(subfield[1]) + "</dummy>"
        data = parseString(data).firstChild
        for child in data.childNodes:
            field.appendChild(child.cloneNode(child))
        datafield.appendChild(field)
    if controlfield_value:
        controlfield = doc.createElement('controlfield')
        controlfield.setAttribute('tag', tag)
        controlfield.appendChild(doc.createTextNode(controlfield_value))
        rec.appendChild(controlfield)
    else:
        rec.appendChild(datafield)
    return rec


def record_xml_output(rec):
    ret = rec.toxml()
    ret = ret.replace('</datafield>', '  </datafield>\n')
    ret = re.sub(r'<datafield(.*?)>', r'  <datafield\1>\n', ret)
    ret = ret.replace('</subfield>', '</subfield>\n')
    ret = ret.replace('<subfield', '    <subfield')
    ret = ret.replace('record>', 'record>\n')
    return ret


def escape_for_xml(data):
    """Transform & to XML valid &amp;."""
    data = re.sub("&(?!(amp|lt|gt);)", "&amp;", data)
    data = re.sub("<(?=[\=\d\.\s])", "&lt;", data)
    return data


def format_arxiv_id(arxiv_id, INSPIRE=False):
    if arxiv_id and not "/" in arxiv_id and "arXiv" not in arxiv_id:
        return "arXiv:%s" % (arxiv_id,)
    elif INSPIRE and arxiv_id and not '.' in arxiv_id \
            and arxiv_id.lower().startswith('arxiv:'):
        return arxiv_id[6:]
    else:
        return arxiv_id


def collapse_initials(name):
    """ Removes the space between initials.
        eg T. A. --> T.A."""
    if len(name.split()) > 1:
        name = re.sub(r'([A-Z]\.) +(?=[A-Z]\.)', r'\1', name)
    return name


def fix_journal_name(journal, knowledge_base):
    """ Converts journal name to Inspire's short form """
    if not journal:
        return '', ''
    if len(journal) < 2:
        return journal, ''
    volume = ''
    if (journal[-1] <= 'Z' and journal[-1] >= 'A') \
            and (journal[-2] == '.' or journal[-2] == ' '):
        volume += journal[-1]
        journal = journal[:-1]
    try:
        journal = journal.strip()
        journal = knowledge_base[journal.upper()].strip()
    except KeyError:
        try:
            journal = knowledge_base[journal].strip()
        except KeyError:
            pass
    journal = journal.replace('. ', '.')
    return journal, volume
