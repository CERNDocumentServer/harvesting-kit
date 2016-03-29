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

from datetime import datetime

from ..bibrecord import (record_get_field_instances,
                         record_add_field,
                         record_get_field_values,
                         record_delete_field,
                         record_delete_fields,
                         field_get_subfield_instances,
                         field_swap_subfields,
                         field_get_subfields)

from ..utils import (
    convert_date_from_iso_to_human,
    return_letters_from_string
)

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
            "PREPRINT": "11",
            "ANNOUNCEMENT": "41",
        }
        self.recid = None
        self.conference_recid = None
        self.conference_codes = None
        self.conference_pages = None

    def get_cnums(self):
        return record_get_field_values(self.record, tag="773", code="w")

    def update_conference_info(self):
        if self.conference_recid:
            subfields = [("b", str(self.conference_recid))]
            if self.conference_codes:
                subfields.append(("n", self.conference_codes[0]))
            if self.conference_pages:
                subfields.append(("k", self.conference_pages[0]))
            record_add_field(self.record, "962", subfields=subfields)

    def update_conference_111(self):
        scn_111_fields = record_get_field_instances(self.record, '111')
        record_delete_fields(self.record, tag="111")
        new_fields = []
        for field in scn_111_fields:
            subs = field_get_subfields(field)
            new_subs = []
            month = ""
            day = ""
            year = ""
            place = ""
            start_date = ""
            end_date = ""
            for code, values in subs.iteritems():
                if not values:
                    continue
                if code == 'g':
                    record_add_field(self.record, tag="035",
                                     subfields=[('9', 'Inspire-CNUM'),
                                                ('a', values[0])])
                elif code == "x":
                    date = values[0].split('-')
                    if len(date) >= 1:
                        year = date[0]
                    if len(date) >= 2:
                        month = date[1]
                    if len(date) >= 3:
                        day = date[2]
                    date_stripped = "".join(date)
                    new_subs.append(("9", date_stripped))
                    if len(date_stripped) == 8:
                        start_date = date_stripped

                    if year:
                        new_subs.append(("f", year))
                        record_add_field(self.record, tag="260",
                                         subfields=[('c', year)])
                elif code == "y":
                    date_stripped = "".join(values[0].split('-'))
                    new_subs.append(("z", date_stripped))
                    if len(date_stripped) == 8:
                        end_date = date_stripped
                elif code == "c":
                    place_parts = [v.strip() for v in values[0].split(',')]
                    if place_parts:
                        place = place_parts[0].lower()
                    new_subs.append((code, values[0]))
                else:
                    new_subs.append((code, values[0]))

            if new_subs:
                if day and month and year and place:
                    new_subs.append(
                        ('g', "{0}{1}{2}{3}".format(place, year, month, day))
                    )
                if start_date and end_date:
                    if end_date[4:6] == start_date[4:6]:
                        # same month
                        date_format = "{0}-{1}".format(
                            start_date[-2:],
                            datetime.strptime(end_date, '%Y%m%d').strftime('%d %b %Y')
                        )
                    else:
                        date_format = "{0}-{1}".format(
                            datetime.strptime(start_date, '%Y%m%d').strftime('%d %b'),
                            datetime.strptime(end_date, '%Y%m%d').strftime('%d %b %Y')
                        )
                    new_subs.append(
                        ('d', date_format)
                    )
                record_add_field(self.record,
                                 tag="111",
                                 subfields=new_subs)

    def update_conference_links(self):
        scn_856_fields = record_get_field_instances(self.record,
                                                    tag='856',
                                                    ind1="4")
        new_fields = []
        for field in scn_856_fields:
            subs = field_get_subfields(field)
            new_subs = []
            if 'y' not in subs:
                new_subs.append(('y', 'Conference home page'))
            for code, values in subs.iteritems():
                new_subs.append((code, values[0]))
            new_fields.append(new_subs)

        record_delete_fields(self.record, tag="856")
        for field in new_fields:
            record_add_field(self.record, tag="856", ind1="4", subfields=field)

    def get_record(self):
        """Override the base."""
        self.recid = self.get_recid()
        self.remove_controlfields()
        self.update_system_numbers()
        self.add_systemnumber("Inspire", recid=self.recid)
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
        self.update_date()
        self.update_date_year()
        self.update_hidden_notes()
        self.update_oai_info()
        self.update_cnum()
        self.update_conference_info()

        self.fields_list = [
            "909", "541", "961",
            "970", "690", "695",
            "981",
        ]
        self.strip_fields()

        if "ANNOUNCEMENT" in self.collections:
            self.update_conference_111()
            self.update_conference_links()
            record_add_field(self.record, "690", ind1="C", subfields=[("a", "CONFERENCE")])

        if "THESIS" in self.collections:
            self.update_thesis_information()
            self.update_thesis_supervisors()

        if "PROCEEDINGS" in self.collections:
            # Special proceeding syntax
            self.update_title_to_proceeding()
            self.update_author_to_proceeding()
            record_add_field(self.record, "690", ind1="C", subfields=[("a", "CONFERENCE")])

        # 690 tags
        if self.tag_as_cern:
            record_add_field(self.record, "690", ind1="C", subfields=[("a", "CERN")])

        return self.record

    def update_oai_info(self):
        """Add the 909 OAI info to 035."""
        for field in record_get_field_instances(self.record, '909', ind1="C", ind2="O"):
            new_subs = []
            for tag, value in field[0]:
                if tag == "o":
                    new_subs.append(("a", value))
                else:
                    new_subs.append((tag, value))
                if value in ["CERN", "CDS", "ForCDS"]:
                    self.tag_as_cern = True
            record_add_field(self.record, '024', ind1="8", subfields=new_subs)
        record_delete_fields(self.record, '909')

    def update_cnum(self):
        """Check if we shall add cnum in 035."""
        if "ConferencePaper" not in self.collections:
            cnums = record_get_field_values(self.record, '773', code="w")
            for cnum in cnums:
                cnum_subs = [
                    ("9", "INSPIRE-CNUM"),
                    ("a", cnum)
                ]
                record_add_field(self.record, "035", subfields=cnum_subs)

    def update_hidden_notes(self):
        """Remove hidden notes and tag a CERN if detected."""
        if not self.tag_as_cern:
            notes = record_get_field_instances(self.record,
                                               tag="595")
            for field in notes:
                for dummy, value in field[0]:
                    if value == "CDS":
                        self.tag_as_cern = True
        record_delete_fields(self.record, tag="595")

    def update_system_numbers(self):
        """035 Externals."""
        scn_035_fields = record_get_field_instances(self.record, '035')
        new_fields = []
        for field in scn_035_fields:
            subs = field_get_subfields(field)
            if '9' in subs:
                if subs['9'][0].lower() == "cds" and subs.get('a'):
                    self.add_control_number("001", subs.get('a')[0])
                if subs['9'][0].lower() in ["inspire", "spirestex", "inspiretex", "desy", "cds"]:
                    continue
            new_fields.append(field_get_subfield_instances(field))
        record_delete_fields(self.record, tag="035")
        for field in new_fields:
            record_add_field(self.record, tag="035", subfields=field)

    def update_collections(self):
        """Try to determine which collections this record should belong to."""
        for value in record_get_field_values(self.record, '980', code='a'):
            if 'NOTE' in value.upper():
                self.collections.add('NOTE')
            if 'THESIS' in value.upper():
                self.collections.add('THESIS')

            if 'PUBLISHED' in value.upper():
                self.collections.add('ARTICLE')

            if 'CONFERENCES' in value.upper():
                self.collections.add('ANNOUNCEMENT')

            if 'PROCEEDINGS' in value.upper():
                self.collections.add('PROCEEDINGS')
            elif 'CONFERENCEPAPER' in value.upper() and \
                 "ConferencePaper" not in self.collections:
                self.collections.add('ConferencePaper')
                if self.is_published() and "ARTICLE" not in self.collections:
                    self.collections.add('ARTICLE')
                else:
                    self.collections.add('PREPRINT')

            if "HIDDEN" in value.upper():
                self.hidden = True

        # Clear out any existing ones.
        record_delete_fields(self.record, "980")

        if not self.collections:
            self.collections.add('PREPRINT')

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
            experiment = acc_experiment[-1]

            # Handle special case of leading experiments numbers NA-050 -> NA 50
            e_suffix = ""
            if "-NA-" in experiment or \
               "-RD-" in experiment or \
               "-WA-" in experiment:
                splitted_experiment = experiment.split("-")
                e_suffix = "-".join(splitted_experiment[2:])
                if e_suffix.startswith("0"):
                    e_suffix = e_suffix[1:]
                experiment = "-".join(splitted_experiment[:2])  # only CERN-NA

            translated_experiment = self.get_config_item(experiment,
                                                         "experiments")
            if not translated_experiment:
                continue
            new_subs = []
            if "---" in translated_experiment:
                experiment_a, experiment_e = translated_experiment.split("---")
                new_subs.append(("a", experiment_a.replace("-", " ")))
            else:
                experiment_e = translated_experiment
            new_subs.append(("e", experiment_e.replace("-", " ") + e_suffix))
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
                elif key == 'v':
                    del field[0][idx]
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
            volume_letter = ""
            journal_name = ""
            for idx, (key, value) in enumerate(subs):
                if key == 'p':
                    journal_name = self.get_config_item(value, "journals")
                    # Make sure journal names have the form (dot)(space) (I know it's horrible)
                    journal_name = journal_name.replace('. ', '.').replace('.', '. ').replace('. ,', '.,').strip()
                elif key == 'v':
                    volume_letter = value
                else:
                    new_subs.append((key, value))

            if not journal_name == "PoS":
                # Special handling of journal name and volumes, except PoS
                letter = return_letters_from_string(volume_letter)
                if letter:
                    journal_name = "{0} {1}".format(journal_name, letter)
                    volume_letter = volume_letter.strip(letter)

            if journal_name:
                new_subs.append(("p", journal_name))
            if volume_letter:
                new_subs.append(("v", volume_letter))
            record_delete_field(self.record, tag="773",
                                field_position_global=field[4])
            record_add_field(self.record, "773", subfields=new_subs)

    def update_thesis_supervisors(self):
        """700 -> 701 Thesis supervisors."""
        for field in record_get_field_instances(self.record, '701'):
            subs = list(field[0])
            subs.append(("e", "dir."))
            record_add_field(self.record, '700', subfields=subs)
        record_delete_fields(self.record, '701')

    def update_thesis_information(self):
        """501 degree info - move subfields."""
        fields_501 = record_get_field_instances(self.record, '502')
        for field in fields_501:
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
            record_delete_field(self.record, tag="502",
                                field_position_global=field[4])
            record_add_field(self.record, "502", subfields=new_subs)

    def update_pagenumber(self):
        """300 page number."""
        pages = record_get_field_instances(self.record, '300')
        for field in pages:
            for idx, (key, value) in enumerate(field[0]):
                if key == 'a':
                    field[0][idx] = ('a', "{0} p".format(value))

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

    def update_date_year(self):
        """260 Date normalization."""
        dates = record_get_field_instances(self.record, '260')
        for field in dates:
            for idx, (key, value) in enumerate(field[0]):
                if key == 'c':
                    field[0][idx] = ('c', value[:4])
                elif key == 't':
                    del field[0][idx]
        if not dates:
            published_years = record_get_field_values(self.record, "773", code="y")
            if published_years:
                record_add_field(
                    self.record, "260", subfields=[("c", published_years[0][:4])])
            else:
                other_years = record_get_field_values(self.record, "269", code="c")
                if other_years:
                    record_add_field(
                        self.record, "260", subfields=[("c", other_years[0][:4])])

    def is_published(self):
        """Check fields 980 and 773 to see if the record has already been published.

        :return: True is published, else False
        """
        field773 = record_get_field_instances(self.record, '773')
        for f773 in field773:
            if 'c' in field_get_subfields(f773):
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
            else:
                # Remove $w
                for idx, (key, value) in enumerate(field[0]):
                    if key == 'w':
                        del field[0][idx]

    def update_languages(self):
        """041 Language."""
        language_fields = record_get_field_instances(self.record, '041')
        language = "eng"
        record_delete_fields(self.record, "041")
        for field in language_fields:
            subs = field_get_subfields(field)
            if 'a' in subs:
                language = self.get_config_item(subs['a'][0], "languages")
                break
        new_subs = [('a', language)]
        record_add_field(self.record, "041", subfields=new_subs)
