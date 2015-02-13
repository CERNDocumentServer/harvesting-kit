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

"""Contains conversion package from INSPIRE to CDS MARCXML.

>>> from harvestingkit.bibrecord import BibRecordPackage
>>> from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS
>>> bibrecs = BibRecordPackage("inspire.xml")
>>> bibrecs.parse()
>>> cds_xml = Inspire2CDS.convert(bibrecs.get_records())
"""

from __future__ import print_function

from ..bibrecord import (record_get_field_instances,
                         record_add_field,
                         record_get_field_values,
                         record_delete_field,
                         record_delete_fields,
                         field_get_subfield_instances,
                         field_swap_subfields,
                         field_get_subfields)

from ..utils import convert_date_from_iso_to_human

from .base import MARCXMLConversion


class Inspire2CDS(MARCXMLConversion):

    """Convert INSPIRE to CDS."""

    # By setting the class variable here, we run it only once a session
    kbs = MARCXMLConversion.load_config("inspire", "cds")

    def __init__(self, bibrec, strip_fields_list=None):
        """Create."""
        super(Inspire2CDS, self).__init__(bibrec, strip_fields_list)
        self.collections = set([])
        self.tag_as_cern = False
        self.collection_base = {
            "PROCEEDINGS": "43",
            "ARTICLE": "13",
            "THESIS": "14",
            "PREPRINT": "11"
        }

    def get_record(self):
        """Override the base."""
        self.update_system_numbers()
        self.add_systemnumber("Inspire")
        self.remove_controlfields()
        self.add_control_number("003", "SzGeCERN")
        self.update_collections()
        self.update_languages()
        self.update_reportnumbers()
        self.update_authors()
        self.update_journals()
        self.update_subject_categories("INSPIRE", "SzGeCERN", "categories_cds")
        self.update_pagenumber()
        self.update_notes()
        self.update_experiments()
        self.update_isbn()
        self.update_links_and_ffts()
        if "THESIS" in self.collections:
            self.update_thesis_information()
            self.update_thesis_supervisors()

        if "PROCEEDINGS" in self.collections:
            # Special proceeding syntax
            self.update_title_to_proceeding()
            self.update_author_to_proceeding()

        # 690 tags
        if self.tag_as_cern:
            record_add_field(self.record, "690", ind1="C", subfields=[("a", "CERN")])

        self.fields_list = [
            "909", "541", "961",
            "970", "690", "595",
            "695",
        ]
        self.strip_fields()
        return self.record

    def update_system_numbers(self):
        """035 Externals."""
        scn_035_fields = record_get_field_instances(self.record, '035')
        for field in scn_035_fields:
            subs = field_get_subfields(field)
            if '9' in subs:
                for sub in subs['9']:
                    if sub.lower() in ["inspire", "spirestex", "inspiretex", "desy"]:
                        record_delete_field(self.record, tag="035",
                                            field_position_global=field[4])

    def update_collections(self):
        """Try to determine which collections this record should belong to."""
        for value in record_get_field_values(self.record, '980', code='a'):
            if 'NOTE' in value.upper():
                self.collections.add('NOTE')
            if 'THESIS' in value.upper():
                self.collections.add('THESIS')

            if 'PROCEEDINGS' in value.upper():
                self.collections.add('PROCEEDINGS')
            elif 'CONFERENCEPAPER' in value.upper():
                self.collections.add('ConferencePaper')

            if "HIDDEN" in value.upper():
                self.hidden = True

        if self.is_published() \
           and "PROCEEDINGS" not in self.collections \
           and "ConferencePaper" not in self.collections:
            self.collections.add("ARTICLE")

        # Clear out any existing ones.
        record_delete_fields(self.record, "980")

        for collection in self.collections:
            record_add_field(self.record,
                             tag='980',
                             subfields=[('a', collection)])
            if collection in self.collection_base:
                subs = [('a', self.collection_base[collection])]
                record_add_field(self.record,
                                 tag='960',
                                 subfields=subs)

    def update_notes(self):
        """Remove INSPIRE specific notes."""
        fields = record_get_field_instances(self.record, '500')
        for field in fields:
            subs = field_get_subfields(field)
            for sub in subs.get('a', []):
                sub = sub.strip()  # remove any spaces before/after
                if sub.startswith("*") and sub.endswith("*"):
                    record_delete_field(self.record, tag="500",
                                        field_position_global=field[4])

    def update_title_to_proceeding(self):
        """Move title info from 245 to 111 proceeding style."""
        titles = record_get_field_instances(self.record,
                                            tag="245")
        for title in titles:
            subs = field_get_subfields(title)
            new_subs = []
            if "a" in subs:
                new_subs.append(("a", subs['a'][0]))
            if "b" in subs:
                new_subs.append(("c", subs['b'][0]))
            record_add_field(self.record,
                             tag="111",
                             subfields=new_subs)
        record_delete_fields(self.record, tag="245")
        record_delete_fields(self.record, tag="246")

    def update_author_to_proceeding(self):
        """Move author info from 245 to 111 proceeding style."""
        titles = record_get_field_instances(self.record,
                                            tag="245")
        for title in titles:
            subs = field_get_subfields(title)
            new_subs = []
            if "a" in subs:
                new_subs.append(("a", subs['a'][0]))
            if "b" in subs:
                new_subs.append(("c", subs['b'][0]))
            record_add_field(self.record,
                             tag="111",
                             subfields=new_subs)
        record_delete_fields(self.record, tag="245")
        record_delete_fields(self.record, tag="246")

    def update_experiments(self):
        """Experiment mapping."""
        # 693 Remove if 'not applicable'
        for field in record_get_field_instances(self.record, '693'):
            subs = field_get_subfields(field)
            acc_experiment = subs.get("e", [])
            if not acc_experiment:
                acc_experiment = subs.get("a", [])
                if not acc_experiment:
                    continue
            translated_experiment = self.get_config_item(acc_experiment[-1],
                                                         "experiments")
            if not translated_experiment:
                continue
            new_subs = []
            if "---" in translated_experiment:
                experiment_a, experiment_e = translated_experiment.split("---")
                new_subs.append(("a", experiment_a.replace("-", " ")))
            else:
                experiment_e = translated_experiment
            new_subs.append(("e", experiment_e.replace("-", " ")))
            record_delete_field(self.record, tag="693",
                                field_position_global=field[4])
            record_add_field(self.record, "693", subfields=new_subs)

    def update_reportnumbers(self):
        """Update reportnumbers."""
        report_037_fields = record_get_field_instances(self.record, '037')
        for field in report_037_fields:
            subs = field_get_subfields(field)
            for val in subs.get("a", []):
                if "arXiv" not in val:
                    record_delete_field(self.record,
                                        tag="037",
                                        field_position_global=field[4])
                    new_subs = [(code, val[0]) for code, val in subs.items()]
                    record_add_field(self.record, "088", subfields=new_subs)
                    break

    def update_authors(self):
        """100 & 700 punctuate author names."""
        author_names = record_get_field_instances(self.record, '100')
        author_names.extend(record_get_field_instances(self.record, '700'))
        for field in author_names:
            subs = field_get_subfields(field)
            for idx, (key, value) in enumerate(field[0]):
                if key == 'a':
                    field[0][idx] = ('a', value.replace(".", " ").strip())
            if subs.get("u", None) == "CERN":
                self.tag_as_cern = True

    def update_isbn(self):
        """Remove dashes from ISBN."""
        isbns = record_get_field_instances(self.record, '020')
        for field in isbns:
            for idx, (key, value) in enumerate(field[0]):
                if key == 'a':
                    field[0][idx] = ('a', value.replace("-", "").strip())

    def update_journals(self):
        """773 journal translations."""
        for field in record_get_field_instances(self.record, '773'):
            subs = field_get_subfield_instances(field)
            new_subs = []
            cnum_subs = []
            for idx, (key, value) in enumerate(subs):
                if key == 'p':
                    new_subs.append(
                        (key, self.get_config_item(value, "journals")))
                else:
                    new_subs.append((key, value))
                    if key == "w":
                        cnum_subs = [
                            ("9", "INSPIRE-CNUM"),
                            ("a", value)
                        ]
            record_delete_field(self.record, tag="773",
                                field_position_global=field[4])
            record_add_field(self.record, "773", subfields=new_subs)
            if cnum_subs:
                record_add_field(self.record, "035", subfields=cnum_subs)

    def update_thesis_supervisors(self):
        """700 -> 701 Thesis supervisors."""
        for field in record_get_field_instances(self.record, '700'):
            record_add_field(self.record, '701', subfields=field[0])
        record_delete_fields(self.record, '700')

    def update_thesis_information(self):
        """501 degree info - move subfields."""
        fields_501 = record_get_field_instances(self.record, '502')
        for idx, field in enumerate(fields_501):
            new_subs = []
            for key, value in field[0]:
                if key == 'b':
                    new_subs.append(('a', value))
                elif key == 'c':
                    new_subs.append(('b', value))
                elif key == 'd':
                    new_subs.append(('c', value))
                else:
                    new_subs.append((key, value))
            fields_501[idx] = field_swap_subfields(field, new_subs)

    def update_pagenumber(self):
        """300 page number."""
        fields_300 = record_get_field_instances(self.record, '300')
        for idx, field in enumerate(fields_300):
            new_subs = []
            old_subs = field[0]
            for code, value in old_subs:
                if code == "a":
                    new_subs.append((
                        "a",
                        "%s p" % (value,)
                    ))
                else:
                    new_subs.append((code, value))
            fields_300[idx] = field_swap_subfields(field, new_subs)

    def update_date(self):
        """269 Date normalization."""
        dates_269 = record_get_field_instances(self.record, '269')
        for idx, field in enumerate(dates_269):
            new_subs = []
            old_subs = field[0]
            for code, value in old_subs:
                if code == "c":
                    new_subs.append((
                        "c",
                        convert_date_from_iso_to_human(value)
                    ))
                else:
                    new_subs.append((code, value))
            dates_269[idx] = field_swap_subfields(field, new_subs)

        published_years = record_get_field_values(self.record, "773", code="y")
        if published_years:
            record_add_field(
                self.record, "260", subfields=[("c", published_years[0])])
        else:
            other_years = record_get_field_values(self.record, "269", code="c")
            if other_years:
                record_add_field(
                    self.record, "260", subfields=[("c", other_years[0][:4])])

    def is_published(self):
        """Check fields 980 and 773 to see if the record has already been published.

        :return: True is published, else False
        """
        field980 = record_get_field_instances(self.record, '980')
        field773 = record_get_field_instances(self.record, '773')
        for f980 in field980:
            if 'a' in field_get_subfields(f980):
                for f773 in field773:
                    if 'p' in field_get_subfields(f773):
                        return True
        return False

    def update_links_and_ffts(self):
        """FFT (856) Dealing with files."""
        for field in record_get_field_instances(self.record,
                                                tag='856',
                                                ind1='4'):
            subs = field_get_subfields(field)
            newsubs = []
            url = subs.get("u", [])

            if not url:
                record_delete_field(self.record, '856', ind1='4',
                                    field_position_global=field[4])
                continue
            url = url[0]
            if "inspirehep.net/record" in url and url.endswith("pdf"):
                # We have an FFT from INSPIRE
                newsubs.append(('a', url))
                description = subs.get("y", [])
                if description:
                    newsubs.append(('d', description[0]))
                if newsubs:
                    record_add_field(self.record, 'FFT', subfields=newsubs)
                    record_delete_field(self.record, '856', ind1='4',
                                        field_position_global=field[4])
