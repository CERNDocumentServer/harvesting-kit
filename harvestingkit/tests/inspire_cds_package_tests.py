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
# along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Tests for inspire_cds_package."""

import os
import unittest
import pkg_resources


class TestConversions(unittest.TestCase):

    """Test simple functionality."""

    def setUp(self):
        """Load demo data."""
        self.inspire_demo_data_path_oai = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire_oai.xml')
        )
        self.inspire_demo_data_path = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire.xml')
        )

    def test_record_parsing(self):
        """Test parsing of sample file."""
        from harvestingkit.bibrecord import BibRecordPackage

        bibrecs = BibRecordPackage(self.inspire_demo_data_path_oai)
        bibrecs.parse()
        self.assertEqual(len(bibrecs.get_records()), 5)

    def test_record_config_load(self):
        """Test loading of kbs."""
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS
        from harvestingkit.inspire_cds_package.from_cds import CDS2Inspire

        conversion = Inspire2CDS({})
        self.assertTrue(conversion.kbs)
        self.assertEqual(
            conversion.get_config_item("Dutch", "languages"),
            "dut"
        )

        conversion = CDS2Inspire({})
        self.assertTrue(conversion.kbs)
        self.assertEqual(
            conversion.get_config_item("Inf. Sci.", "journals"),
            "Info.Sci."
        )

    def test_multiple_conversions(self):
        """Test conversion of multiple records."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        bibrecs = BibRecordPackage(self.inspire_demo_data_path_oai)
        bibrecs.parse()
        xml = Inspire2CDS.convert_all(bibrecs.get_records())
        self.assertEqual(xml.count("</record>"), 5)
        self.assertEqual(xml.count('<controlfield tag="003">SzGeCERN</controlfield>'), 5)

    def test_non_oai_conversion(self):
        """Test conversion of non-OAI-PMH input MARCXML."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        xml = Inspire2CDS.convert_all(bibrecs.get_records())
        self.assertEqual(xml.count("</record>"), 9)
        self.assertEqual(xml.count('<controlfield tag="003">SzGeCERN</controlfield>'), 9)

    def test_single_conversion(self):
        """Test conversion of non-OAI-PMH input MARCXML."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        conversion = Inspire2CDS(bibrecs.get_records()[0])
        xml = conversion.convert()
        self.assertEqual(xml.count("</record>"), 1)
        self.assertEqual(xml.count('<controlfield tag="003">SzGeCERN</controlfield>'), 1)


class TestINSPIRE2CDS(unittest.TestCase):

    """Test converted record data."""

    def setUp(self):
        """Load demo data."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        self.inspire_demo_data_path = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire_oai.xml')
        )

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        self.parsed_record = bibrecs.get_records()[0]
        self.package = Inspire2CDS(self.parsed_record)
        self.recid = self.package.get_recid()
        self.converted_record = self.package.get_record()

    def test_double_conversion(self):
        """Test that calling things twice does not alter results."""
        self.assertEqual(self.converted_record,
                         self.package.get_record())

    def test_inspire_id(self):
        """Test for INSPIRE ID in 035."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="a",
                                    filter_subfield_code="a",
                                    filter_subfield_value=self.recid,
                                    filter_subfield_mode="e")
        )

    def test_subject(self):
        """Test for subject in 65017."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="650", ind1="1", ind2="7",
                                    code="a",
                                    filter_subfield_code="a",
                                    filter_subfield_value="Detectors and Experimental Techniques",
                                    filter_subfield_mode="e")
        )

    def test_notex(self):
        """Make sure that no SPIRES/INSPIRE TeX code is there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="9",
                                    filter_subfield_code="9",
                                    filter_subfield_value="INSPIRETeX",
                                    filter_subfield_mode="e")
        )

    def test_nodesy(self):
        """Make sure that no DESY fields are there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="9",
                                    filter_subfield_code="9",
                                    filter_subfield_value="DESY",
                                    filter_subfield_mode="e")
        )

    def test_nohiddenfield(self):
        """Make sure that no hidden INSPIRE field is there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="595",
                                    code="%")
        )

    def test_noinspirenotes(self):
        """Make sure that no INSPIRE specific notes are there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="500",
                                    code="a",
                                    filter_subfield_code="a",
                                    filter_subfield_value="*Brief entry*",
                                    filter_subfield_mode="s")
        )
        # Some notes should be there
        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="500",
                                    code="a")
        )

    def test_experiments(self):
        """Test for correct experiments values in 693."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="693",
                                    code="a"),
            ["CERN LHC"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="693",
                                    code="e"),
            ["CMS"]
        )

    def test_isbn(self):
        """Test for correct ISBN."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="020",
                                    code="a"),
            ["9785949900109"]
        )

    def test_fft(self):
        """Test for existence of FFT on PDF URL."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="FFT",
                                    code="a")
        )
        # Some other URL should be there
        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="856",
                                    ind1="4",
                                    code="u")
        )


class TestINSPIRE2CDSProceeding(unittest.TestCase):

    """Test converted record data."""

    def setUp(self):
        """Load demo data."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        self.inspire_demo_data_path = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire_oai.xml')
        )

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        parsed_record = bibrecs.get_records()[1]
        self.package = Inspire2CDS(parsed_record)
        self.recid = self.package.get_recid()
        self.converted_record = self.package.get_record()

    def test_cnum(self):
        """Make sure that CNUM is okay."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="773",
                                    code="w",
                                    filter_subfield_code="w",
                                    filter_subfield_value="C96-05-21",
                                    filter_subfield_mode="e")
        )
        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="a",
                                    filter_subfield_code="9",
                                    filter_subfield_value="INSPIRE-CNUM",
                                    filter_subfield_mode="e")
        )

    def test_noinspirekeywords(self):
        """Make sure that no INSPIRE keywords are there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="695",
                                    code="2",
                                    filter_subfield_code="2",
                                    filter_subfield_value="INSPIRE",
                                    filter_subfield_mode="e")
        )

    def test_collectionname(self):
        """Make sure that the right collection name is there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="980",
                                    code="a",
                                    filter_subfield_code="a",
                                    filter_subfield_value="ConferencePaper",
                                    filter_subfield_mode="e")
        )


if __name__ == '__main__':
    unittest.main()
