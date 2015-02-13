# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2013, 2014, 2015 CERN.
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
## along with Harvesting Kit; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Set of utilities for ElementTree XML parsing."""

from xml.etree import ElementTree as ET


def get_request_subfields(root):
    """Build a basic 035 subfield with basic information from the OAI-PMH request.

    :param root: ElementTree root node

    :return: list of subfield tuples [(..),(..)]
    """
    request = root.find('request')
    responsedate = root.find('responseDate')

    subs = [("9", request.text),
            ("h", responsedate.text),
            ("m", request.attrib["metadataPrefix"])]
    return subs


def strip_xml_namespace(root):
    """Strip out namespace data from an ElementTree.

    This function is recursive and will traverse all
    subnodes to the root element

    @param root: the root element

    @return: the same root element, minus namespace
    """
    try:
        root.tag = root.tag.split('}')[1]
    except IndexError:
        pass

    for element in root.getchildren():
        strip_xml_namespace(element)


def element_tree_collection_to_records(tree):
    """Take an ElementTree and converts the nodes into BibRecord records.

    This function is for a tree root of collection as such:
    <collection>
        <record>
            <!-- MARCXML -->
        </record>
        <record> ... </record>
    </collection>
    """
    from .bibrecord import create_record

    records = []
    collection = tree.getroot()
    for record_element in collection.getchildren():
        marcxml = ET.tostring(record_element, encoding="utf-8")
        record, status, errors = create_record(marcxml)
        if errors:
            print(str(status))
        records.append(record)
    return records


def element_tree_oai_records(tree, header_subs=None):
    """Take an ElementTree and converts the nodes into BibRecord records.

    This expects a clean OAI response with the tree root as ListRecords
    or GetRecord and record as the subtag like so:
    <ListRecords|GetRecord>
        <record>
            <header>
                <!-- Record Information -->
            </header>
            <metadata>
                <record>
                    <!-- MARCXML -->
                </record>
            </metadata>
        </record>
        <record> ... </record>
    </ListRecords|GetRecord>

    :param tree: ElementTree object corresponding to GetRecord node from
                 OAI request
    :param header_subs: OAI header subfields, if any

    :yield: (record, is_deleted) A tuple, with first a BibRecord found and
             second a boolean value saying if this is a deleted record or not.
    """
    from .bibrecord import record_add_field, create_record

    if not header_subs:
        header_subs = []
    # Make it a tuple, this information should not be changed
    header_subs = tuple(header_subs)

    oai_records = tree.getroot()
    for record_element in oai_records.getchildren():
        header = record_element.find('header')

        # Add to OAI subfield
        datestamp = header.find('datestamp')
        identifier = header.find('identifier')
        identifier = identifier.text

        # The record's subfield is based on header information
        subs = list(header_subs)
        subs.append(("a", identifier))
        subs.append(("d", datestamp.text))

        if "status" in header.attrib and header.attrib["status"] == "deleted":
            # Record was deleted - create delete record
            deleted_record = {}
            record_add_field(deleted_record, "037", subfields=subs)
            yield deleted_record, True
        else:
            marc_root = record_element.find('metadata').find('record')
            marcxml = ET.tostring(marc_root, encoding="utf-8")
            record, status, errors = create_record(marcxml)
            if status == 1:
                # Add OAI request information
                record_add_field(record, "035", subfields=subs)
                yield record, False
