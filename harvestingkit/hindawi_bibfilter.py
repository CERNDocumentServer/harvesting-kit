# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2013, 2014 CERN.
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

"""
Set of utilities for the SCOAP3 project to parse Hindawi OAI-PMH feeds.
"""

import sys
import os
from xml.dom.minidom import parse

from invenio.bibupload import find_records_from_extoaiid
from harvestingkit.utils import (record_add_field,
                                 record_xml_output,
                                 create_record)
from harvestingkit.minidom_utils import (xml_to_text,
                                         get_value_in_tag)


def get_xml(input=sys.stdin):
    return parse(input)


def create_record_file(filename, records):
    if not records:
        return
    print >> sys.stderr, "Creating %s with %s records" % (filename, len(records))
    marcxml = open(filename, "w")
    print >> marcxml, "<collection>"
    for record in records:
        print >> marcxml, record
    print >> marcxml, "</collection>"


def bibfilter(filename):
    print >> sys.stderr, "Parsing %s" % filename
    xml = get_xml(open(filename))
    request = xml.getElementsByTagName("request")[0].toxml()
    response_date = get_value_in_tag(xml, "responseDate")
    new_records, updated_records = [], []
    records = xml.getElementsByTagName("record")
    print >> sys.stderr, "Found %s records" % len(records)
    for record in records:
        marcxml, new = convert_record(record, response_date, request)
        if marcxml is None:
            continue
        if new:
            new_records.append(marcxml)
        else:
            updated_records.append(marcxml)
    create_record_file(filename + '.insert.xml', new_records)
    create_record_file(filename + '.correct.xml', updated_records)


def convert_record(record, response_date, request):
    header = record.getElementsByTagName("header")[0]
    oai_identifier = get_value_in_tag(header, "identifier")
    datestamp = get_value_in_tag(header, "datestamp")
    status = header.getAttribute("status").encode('utf8')
    rec = create_record()
    record_add_field(rec, tag="035", subfields=[('a', oai_identifier),
                                                ('u', request),
                                                ('9', 'Hindawi'),
                                                ('d', datestamp),
                                                ('h', response_date),
                                                ('m', 'marc21'),
                                                ('t', 'false')])
    new = True
    if find_records_from_extoaiid(oai_identifier, 'Hindawi'):
        new = False
    if status == 'deleted':
        if new:
            ## deleting a record we didn't have? Who cares :-)
            return None, True
        else:
            record_add_field(rec, tag="980", subfields=[('a', 'SCOAP3'), ('b', 'Hindawi'), ('c', 'DELETED')])
            return record_xml_output(rec), False
    for datafield in record.getElementsByTagName("datafield"):
        tag = datafield.getAttribute("tag").encode('utf-8')
        ind1 = datafield.getAttribute("ind1").encode('utf-8') or ' '
        ind2 = datafield.getAttribute("ind2").encode('utf-8') or ' '
        subfields = []
        for subfield in datafield.getElementsByTagName("subfield"):
            code = subfield.getAttribute("code").encode('utf-8')
            value = xml_to_text(subfield)
            subfields.append((code, value))
        record_add_field(rec, tag=tag, ind1=ind1, ind2=ind2, subfields=subfields)
    return record_xml_output(rec), new


def main():
    if len(sys.argv) == 2 and os.path.exists(sys.argv[1]):
        ## Executed in bibfilter mode.
        try:
            bibfilter(sys.argv[1])
        except:
            from invenio.errorlib import register_exception
            register_exception(alert_admin=True)
            raise

if __name__ == "__main__":
    main()
