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

"""Contains conversion package from CDS to INSPIRE MARCXML.

>>> from harvestingkit.bibrecord import BibRecordPackage
>>> from harvestingkit.inspire_cds_package.from_cds import CDS2Inspire
>>> bibrecs = BibRecordPackage("cds.xml")
>>> bibrecs.parse()
>>> inspire_xml = CDS2Inspire.convert(bibrecs.get_records())
"""

from __future__ import print_function

import os
import re

from tempfile import mkstemp

from ..bibrecord import (record_get_field_instances,
                         record_add_field,
                         record_get_field_values,
                         record_delete_field,
                         record_delete_fields,
                         record_replace_field,
                         field_get_subfield_instances,
                         create_field,
                         field_swap_subfields,
                         field_get_subfields)

from ..utils import (
    punctuate_authorname,
    convert_images,
    convert_date_to_iso,
    unzip,
    locate,
    download_file,
)
from .base import MARCXMLConversion


class CDS2Inspire(MARCXMLConversion):

    """Convert CDS to INSPIRE."""

    # By setting the class variable here, we run it only once a session
    kbs = MARCXMLConversion.load_config("cds", "inspire")

    def __init__(self, bibrec, strip_fields_list=None):
        """Create."""
        super(CDS2Inspire, self).__init__(bibrec, strip_fields_list)
        self.collections = set([])

    def get_record(self):
        """Override the base get_record."""
        self.update_system_numbers()
        self.add_systemnumber("CDS")
        self.fields_list = [
            "024", "041", "035", "037", "088", "100",
            "110", "111", "242", "245", "246", "260",
            "269", "300", "502", "650", "653", "693",
            "700", "710", "773", "856", "520", "500",
            "980"
        ]
        self.keep_only_fields()

        self.determine_collections()
        self.add_cms_link()
        self.update_languages()
        self.update_reportnumbers()
        self.update_date()
        self.update_pagenumber()
        self.update_authors()
        self.update_subject_categories("SzGeCERN", "INSPIRE", "categories_inspire")
        self.update_keywords()
        self.update_experiments()
        self.update_collaboration()
        self.update_journals()
        self.update_links_and_ffts()

        if 'THESIS' in self.collections:
            self.update_thesis_supervisors()
            self.update_thesis_information()

        if 'NOTE' in self.collections:
            self.add_notes()

        for collection in self.collections:
            record_add_field(self.record,
                             tag='980',
                             subfields=[('a', collection)])
        self.remove_controlfields()
        return self.record

    def determine_collections(self):
        """Try to determine which collections this record should belong to."""
        for value in record_get_field_values(self.record, '980', code='a'):
            if 'NOTE' in value.upper():
                self.collections.add('NOTE')
            if 'THESIS' in value.upper():
                self.collections.add('THESIS')
            if 'CONFERENCEPAPER' in value.upper():
                self.collections.add('ConferencePaper')
            if "HIDDEN" in value.upper():
                self.hidden = True

        if self.is_published():
            self.collections.add("PUBLISHED")
            self.collections.add("CITEABLE")

        if 'NOTE' not in self.collections:
            from itertools import product
            # TODO: Move this to a KB
            kb = ['ATLAS-CONF-', 'CMS-PAS-', 'ATL-', 'CMS-DP-',
                  'ALICE-INT-', 'LHCb-PUB-']
            values = record_get_field_values(self.record, "088", code='a')
            for val, rep in product(values, kb):
                if val.startswith(rep):
                    self.collections.add('NOTE')
                    break

        # 980 Arxiv tag
        if record_get_field_values(self.record, '035',
                                   filter_subfield_code="a",
                                   filter_subfield_value="arXiv"):
            self.collections.add("arXiv")

        # 980 HEP && CORE
        self.collections.add('HEP')
        self.collections.add('CORE')

        # 980 Conference Note
        if 'ConferencePaper' not in self.collections:
            for value in record_get_field_values(self.record,
                                                 tag='962',
                                                 code='n'):
                if value[-2:].isdigit():
                    self.collections.add('ConferencePaper')
                    break
        # Clear out any existing ones.
        record_delete_fields(self.record, "980")

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

    def add_cms_link(self):
        """Special handling if record is a CMS NOTE."""
        intnote = record_get_field_values(self.record, '690',
                                          filter_subfield_code="a",
                                          filter_subfield_value='INTNOTE')
        if intnote:
            val_088 = record_get_field_values(self.record,
                                              tag='088',
                                              filter_subfield_code="a")
            for val in val_088:
                if 'CMS' in val:
                    url = ('http://weblib.cern.ch/abstract?CERN-CMS' +
                           val.split('CMS', 1)[-1])
                    record_add_field(self.record,
                                     tag='856',
                                     ind1='4',
                                     subfields=[('u', url)])

    def update_system_numbers(self):
        """035 Externals."""
        scn_035_fields = record_get_field_instances(self.record, '035')
        forbidden_values = ["cercer",
                            "inspire",
                            "xx",
                            "cern annual report",
                            "cmscms",
                            "wai01"]
        for field in scn_035_fields:
            subs = field_get_subfields(field)
            if '9' in subs:
                if 'a' not in subs:
                    continue
                for sub in subs['9']:
                    if sub.lower() in forbidden_values:
                        break
                else:
                    # No forbidden values (We did not "break")
                    suffixes = [s.lower() for s in subs['9']]
                    if 'spires' in suffixes:
                        new_subs = [('a', 'SPIRES-%s' % subs['a'][0])]
                        record_add_field(
                            self.record, '970', subfields=new_subs)
                        continue
            if 'a' in subs:
                for sub in subs['a']:
                    if sub.lower() in forbidden_values:
                        record_delete_field(self.record, tag="035",
                                            field_position_global=field[4])

    def update_reportnumbers(self):
        """Handle reportnumbers. """
        rep_088_fields = record_get_field_instances(self.record, '088')
        for field in rep_088_fields:
            subs = field_get_subfields(field)
            if '9' in subs:
                for val in subs['9']:
                    if val.startswith('P0') or val.startswith('CM-P0'):
                        sf = [('9', 'CERN'), ('b', val)]
                        record_add_field(self.record, '595', subfields=sf)
            for key, val in field[0]:
                if key in ['a', '9'] and not val.startswith('SIS-'):
                    record_add_field(
                        self.record, '037', subfields=[('a', val)])
        record_delete_fields(self.record, "088")

        # 037 Externals also...
        rep_037_fields = record_get_field_instances(self.record, '037')
        for field in rep_037_fields:
            subs = field_get_subfields(field)
            if 'a' in subs:
                for value in subs['a']:
                    if 'arXiv' in value:
                        new_subs = [('a', value), ('9', 'arXiv')]
                        for fld in record_get_field_instances(self.record,  '695'):
                            for key, val in field_get_subfield_instances(fld):
                                if key == 'a':
                                    new_subs.append(('c', val))
                                    break
                        nf = create_field(subfields=new_subs)
                        record_replace_field(self.record, '037', nf, field[4])
            for key, val in field[0]:
                if key in ['a', '9'] and val.startswith('SIS-'):
                    record_delete_field(
                        self.record, '037', field_position_global=field[4])

    def update_date(self):
        """269 Date normalization."""
        for field in record_get_field_instances(self.record, '269'):
            for idx, (key, value) in enumerate(field[0]):
                if key == "c":
                    field[0][idx] = ("c", convert_date_to_iso(value))
                    record_delete_fields(self.record, "260")

        if 'THESIS' not in self.collections:
            for field in record_get_field_instances(self.record, '260'):
                record_add_field(self.record, '269', subfields=field[0])
            record_delete_fields(self.record, '260')

    def update_pagenumber(self):
        """300 page number."""
        for field in record_get_field_instances(self.record, '300'):
            for idx, (key, value) in enumerate(field[0]):
                if key == 'a':
                    if "mult." not in value and value != " p":
                        field[0][idx] = ('a', re.sub(r'[^\d-]+', '', value))
                    else:
                        record_delete_field(self.record, '300',
                                            field_position_global=field[4])
                        break

    def update_authors(self):
        """100 & 700 punctuate author names."""
        author_names = record_get_field_instances(self.record, '100')
        author_names.extend(record_get_field_instances(self.record, '700'))
        for field in author_names:
            subs = field_get_subfields(field)
            if 'i' not in subs or 'XX' in subs['i']:
                if 'j' not in subs or 'YY' in subs['j']:
                    for idx, (key, value) in enumerate(field[0]):
                        if key == 'a':
                            field[0][idx] = ('a', punctuate_authorname(value))

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
                if key == 'a':
                    new_subs.append(('b', value))
                elif key == 'b':
                    new_subs.append(('c', value))
                elif key == 'c':
                    new_subs.append(('d', value))
                else:
                    new_subs.append((key, value))
            fields_501[idx] = field_swap_subfields(field, new_subs)

    def update_keywords(self):
        """653 Free Keywords."""
        for field in record_get_field_instances(self.record, '653', ind1='1'):
            subs = field_get_subfields(field)
            new_subs = []
            if 'a' in subs:
                for val in subs['a']:
                    new_subs.extend([('9', 'author'), ('a', val)])
            new_field = create_field(subfields=new_subs, ind1='1')
            record_replace_field(
                self.record, '653', new_field, field_position_global=field[4])

    def update_experiments(self):
        """Experiment mapping."""
        # 693 Remove if 'not applicable'
        for field in record_get_field_instances(self.record, '693'):
            subs = field_get_subfields(field)
            all_subs = subs.get('a', []) + subs.get('e', [])
            if 'not applicable' in [x.lower() for x in all_subs]:
                record_delete_field(self.record, '693',
                                    field_position_global=field[4])
            new_subs = []
            experiment_a = ""
            experiment_e = ""
            for (key, value) in subs.iteritems():
                if key == 'a':
                    experiment_a = value[0]
                    new_subs.append((key, value[0]))
                elif key == 'e':
                    experiment_e = value[0]
            experiment = "%s---%s" % (experiment_a.replace(" ", "-"),
                                      experiment_e)
            translated_experiments = self.get_config_item(experiment,
                                                          "experiments")
            new_subs.append(("e", translated_experiments))
            record_delete_field(self.record, tag="693",
                                field_position_global=field[4])
            record_add_field(self.record, "693", subfields=new_subs)

    def update_collaboration(self):
        """710 Collaboration."""
        for field in record_get_field_instances(self.record, '710'):
            subs = field_get_subfield_instances(field)
            for idx, (key, value) in enumerate(subs[:]):
                if key == '5':
                    subs.pop(idx)
                elif value.startswith('CERN. Geneva'):
                    subs.pop(idx)
            if len(subs) == 0:
                record_delete_field(self.record,
                                    tag='710',
                                    field_position_global=field[4])

    def update_journals(self):
        """773 journal translations."""
        for field in record_get_field_instances(self.record, '773'):
            subs = field_get_subfield_instances(field)
            new_subs = []
            for idx, (key, value) in enumerate(subs):
                if key == 'p':
                    new_subs.append((key, self.get_config_item(value,
                                                               "journals")))
                else:
                    new_subs.append((key, value))
            record_delete_field(self.record, tag="773",
                                field_position_global=field[4])
            record_add_field(self.record, "773", subfields=new_subs)

    def update_links_and_ffts(self):
        """FFT (856) Dealing with graphs."""
        figure_counter = 0
        for field in record_get_field_instances(self.record,
                                                tag='856',
                                                ind1='4'):
            subs = field_get_subfields(field)

            newsubs = []
            remove = False

            if 'z' in subs:
                is_figure = [s for s in subs['z'] if "figure" in s.lower()]
                if is_figure and 'u' in subs:
                    is_subformat = [
                        s for s in subs['u'] if "subformat" in s.lower()]
                    if not is_subformat:
                        url = subs['u'][0]
                        if url.endswith(".pdf"):
                            # We try to convert
                            fd, local_url = mkstemp(suffix=os.path.basename(url))
                            os.close(fd)
                            self.logger.info(
                                "Downloading %s into %s" % (url, local_url))
                            plotfile = ""
                            try:
                                plotfile = download_file(url=url,
                                                         download_to_file=local_url)
                            except Exception as e:
                                self.logger.exception(e)
                                remove = True
                            if plotfile:
                                converted = convert_images([plotfile])
                                if converted:
                                    url = converted.pop()
                                    msg = "Successfully converted %s to %s" \
                                          % (local_url, url)
                                    self.logger.info(msg)
                                else:
                                    msg = "Conversion failed on %s" \
                                          % (local_url,)
                                    self.logger.error(msg)
                                    url = None
                                    remove = True
                        if url:
                            newsubs.append(('a', url))
                            newsubs.append(('t', 'Plot'))
                            figure_counter += 1
                            if 'y' in subs:
                                newsubs.append(
                                    ('d', "%05d %s" % (figure_counter, subs['y'][0])))
                                newsubs.append(('n', subs['y'][0]))
                            else:
                                # Get basename without extension.
                                name = os.path.basename(
                                    os.path.splitext(subs['u'][0])[0])
                                newsubs.append(
                                    ('d', "%05d %s" % (figure_counter, name)))
                                newsubs.append(('n', name))

            if not newsubs and 'u' in subs:
                is_fulltext = [s for s in subs['u'] if ".pdf" in s]
                if is_fulltext:
                    newsubs = [('t', 'INSPIRE-PUBLIC'), ('a', subs['u'][0])]

            if not newsubs and 'u' in subs:
                remove = True
                is_zipfile = [s for s in subs['u'] if ".zip" in s]
                if is_zipfile:
                    url = is_zipfile[0]

                    local_url = os.path.join(self.get_local_folder(), os.path.basename(url))
                    self.logger.info("Downloading %s into %s" %
                                     (url, local_url))
                    zipped_archive = ""
                    try:
                        zipped_archive = download_file(url=is_zipfile[0],
                                                      download_to_file=local_url)
                    except Exception as e:
                        self.logger.exception(e)
                        remove = True
                    if zipped_archive:
                        unzipped_archive = unzip(zipped_archive)
                        list_of_pngs = locate("*.png", unzipped_archive)
                        for png in list_of_pngs:
                            if "_vti_" in png or "__MACOSX" in png:
                                continue
                            figure_counter += 1
                            plotsubs = []
                            plotsubs.append(('a', png))
                            caption = '%05d %s' % (
                                figure_counter, os.path.basename(png))
                            plotsubs.append(('d', caption))
                            plotsubs.append(('t', 'Plot'))
                            record_add_field(
                                self.record, 'FFT', subfields=plotsubs)

            if not remove and not newsubs and 'u' in subs:
                urls = ('http://cdsweb.cern.ch', 'http://cms.cern.ch',
                        'http://cmsdoc.cern.ch', 'http://documents.cern.ch',
                        'http://preprints.cern.ch', 'http://cds.cern.ch')
                for val in subs['u']:
                    if any(url in val for url in urls):
                        remove = True
                        break
                    if val.endswith('ps.gz'):
                        remove = True

            if newsubs:
                record_add_field(self.record, 'FFT', subfields=newsubs)
                remove = True

            if remove:
                record_delete_field(self.record, '856', ind1='4',
                                    field_position_global=field[4])

    def add_notes(self):
        """500 - Preliminary results."""
        subs = [('a', "Preliminary results")]
        record_add_field(self.record, "500", subfields=subs)
