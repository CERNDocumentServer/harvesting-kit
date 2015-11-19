# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2015 CERN.
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
# along with Harvesting Kit; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Contains parsers for MARCXML flavors."""

from __future__ import print_function

from tempfile import mkdtemp

from ..bibrecord import (record_get_field_instances,
                         record_add_field,
                         record_delete_fields,
                         record_strip_controlfields,
                         record_xml_output,
                         field_get_subfields,
                         BibRecordPackage)

from ..utils import create_logger


class MARCXMLConversion(object):

    """Convert a BibRecord from a MARCXML mapping to another."""

    logger = create_logger("harvestingkit.MARCXMLConversion")
    kbs = {}

    def __init__(self, bibrec, strip_fields_list=None):
        """Create an instance of a record conversion."""
        self.record = bibrec
        self.strip_fields_list = strip_fields_list
        self.hidden = False

    @classmethod
    def convert_all(cls, records):
        """Convert the list of bibrecs into one MARCXML.

        >>> from harvestingkit.bibrecord import BibRecordPackage
        >>> from harvestingkit.inspire_cds_package import Inspire2CDS
        >>> bibrecs = BibRecordPackage("inspire.xml")
        >>> bibrecs.parse()
        >>> xml = Inspire2CDS.convert_all(bibrecs.get_records())

        :param records: list of BibRecord dicts
        :type records: list

        :returns: MARCXML as string
        """
        out = ["<collection>"]
        for rec in records:
            conversion = cls(rec)
            out.append(conversion.convert())
        out.append("</collection>")
        return "\n".join(out)

    @classmethod
    def from_source(cls, source):
        """Yield single conversion objects from a MARCXML file or string.

        >>> from harvestingkit.inspire_cds_package import Inspire2CDS
        >>> for record in Inspire2CDS.from_source("inspire.xml"):
        >>>     xml = record.convert()

        """
        bibrecs = BibRecordPackage(source)
        bibrecs.parse()
        for bibrec in bibrecs.get_records():
            yield cls(bibrec)

    @classmethod
    def get_config_item(cls, key, kb_name):
        """Return the opposite mapping by searching the imported KB."""
        config_dict = cls.kbs.get(kb_name, None)
        if config_dict:
            if key in config_dict:
                return config_dict[key]
            else:
                res = [v for k, v in config_dict.items() if key in k]
                if res:
                    return res[0]
        return key

    @staticmethod
    def load_config(from_key, to_key):
        """Load configuration from config.

        Meant to run only once per system process as
        class variable in subclasses."""
        from .mappings import mappings
        kbs = {}
        for key, values in mappings['config'].iteritems():
            parse_dict = {}
            for mapping in values:
                # {'inspire': 'Norwegian', 'cds': 'nno'}
                # -> {"Norwegian": "nno"}
                parse_dict[mapping[from_key]] = mapping[to_key]
            kbs[key] = parse_dict
        return kbs

    def convert(self):
        """Convert current record and return MARCXML.

        >>> from harvestingkit.bibrecord import BibRecordPackage
        >>> from harvestingkit.inspire_cds_package import Inspire2CDS
        >>> bibrecs = BibRecordPackage("inspire.xml")
        >>> bibrecs.parse()
        >>> for bibrec in bibrecs:
        >>>     rec = Inspire2CDS(bibrec)
        >>>     xml = rec.convert(bibrec)

        :returns: MARCXML as string
        """
        self.get_record()
        return self.get_xml()

    def get_record(self):
        """Return the record."""
        return self.record

    def get_xml(self):
        """Return the current record as MARCXML."""
        return record_xml_output(self.record)

    def get_recid(self):
        """Return the record ID from 001."""
        try:
            return self.record['001'][0][3]
        except KeyError:
            return

    def get_local_folder(self):
        """Return a path to a generated local folder."""
        if not hasattr(self, "local_folder"):
            self.local_folder = mkdtemp()
        return self.local_folder

    def match(self, query=None, **kwargs):
        """Try to match the current record to the database."""
        from invenio.search_engine import perform_request_search
        if not query:
            # We use default setup
            recid = self.record["001"][0][3]
            return perform_request_search(p="035:%s" % (recid,),
                                          of="id")
        else:
            if "recid" not in kwargs:
                kwargs["recid"] = self.record["001"][0][3]
            return perform_request_search(p=query % kwargs,
                                          of="id")

    def remove_controlfields(self):
        """Clear any existing control fields."""
        record_strip_controlfields(self.record)

    def keep_only_fields(self):
        """Keep only fields listed in field_list."""
        for tag in self.record.keys():
            if tag not in self.fields_list:
                record_delete_fields(self.record, tag)

    def strip_fields(self):
        """Clear any fields listed in field_list."""
        for tag in self.record.keys():
            if tag in self.fields_list:
                record_delete_fields(self.record, tag)

    def add_systemnumber(self, source, recid=None):
        """Add 035 number from 001 recid with given source."""
        if not recid:
            recid = self.get_recid()
        if not self.hidden and recid:
            record_add_field(
                self.record,
                tag='035',
                subfields=[('9', source), ('a', recid)]
            )

    def add_control_number(self, tag, value):
        """Add a control-number 00x for given tag with value."""
        record_add_field(self.record,
                         tag,
                         controlfield_value=value)

    def update_subject_categories(self, primary, secondary, kb):
        """650 Translate Categories."""
        category_fields = record_get_field_instances(self.record,
                                                     tag='650',
                                                     ind1='1',
                                                     ind2='7')
        record_delete_fields(self.record, "650")
        for field in category_fields:
            for idx, (key, value) in enumerate(field[0]):
                if key == 'a':
                    new_value = self.get_config_item(value, kb)
                    if new_value != value:
                        new_subs = [('2', secondary), ('a', new_value)]
                    else:
                        new_subs = [('2', primary), ('a', value)]
                    record_add_field(self.record, "650", ind1="1", ind2="7",
                                     subfields=new_subs)
                    break

    def update_languages(self):
        """041 Language."""
        language_fields = record_get_field_instances(self.record, '041')
        record_delete_fields(self.record, "041")
        for field in language_fields:
            subs = field_get_subfields(field)
            if 'a' in subs:
                if "eng" in subs['a']:
                    continue
                new_value = self.get_config_item(subs['a'][0], "languages")
                new_subs = [('a', new_value)]
                record_add_field(self.record, "041", subfields=new_subs)
