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
        self.assertEqual(xml.count("</record>"), 3)
        self.assertEqual(xml.count('<controlfield tag="003">SzGeCERN</controlfield>'), 3)

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

    def test_is_not_published(self):
        """Test if published is correct."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        non_published_record = Inspire2CDS(bibrecs.get_records()[0])
        self.assertFalse(non_published_record.is_published())

    def test_is_published(self):
        """Test if published is correct."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        bibrecs = BibRecordPackage(self.inspire_demo_data_path_oai)
        bibrecs.parse()
        non_published_record = Inspire2CDS(bibrecs.get_records()[0])
        self.assertTrue(non_published_record.is_published())


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

    def test_cds_id(self):
        """Test for INSPIRE ID in 035."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertTrue(
            record_get_field_values(self.converted_record,
                                    tag="001")
        )

    def test_pubnote(self):
        """Check that the 773 field is good."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="773",
                                    code="v"),
            ["768"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="773",
                                    code="p"),
            ["Nucl. Instrum. Methods Phys. Res., A"]
        )

    def test_language(self):
        """Test for language."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="041",
                                    code="a"),
            ["eng"]
        )

    def test_page_number(self):
        """Test for page number."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="300",
                                    code="a"),
            ["8 p"]
        )

    def test_date(self):
        """Test for proper date in 260."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="260",
                                    code="c"),
            ["2014"]
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

    def test_nocds(self):
        """Make sure that no CDS fields are there."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="9",
                                    filter_subfield_code="9",
                                    filter_subfield_value="CDS",
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

    def test_cern_tag(self):
        """Test for CERN tag in 690."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="690",
                                    ind1="C",
                                    code="a"),
            ["CERN"]
        )

    def test_oai_tag(self):
        """Test for OAI tag in 035."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="m"),
            ["marcxml"]
        )

    def test_oai_tag_024(self):
        """Test for OAI tag in 024."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="024",
                                    ind1="8",
                                    code="p"),
            ["CERN", "INSPIRE:HEP", "ForCDS"]
        )


class TestINSPIRE2CDSProceeding(unittest.TestCase):

    """Test converted record data."""

    def setUp(self):
        """Load demo data."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        self.inspire_demo_data_path = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire.xml')
        )

        bibrecs = BibRecordPackage(self.inspire_demo_data_path)
        bibrecs.parse()
        self.parsed_record = bibrecs.get_records()[0]
        self.package = Inspire2CDS(self.parsed_record)
        self.recid = self.package.get_recid()
        self.converted_record = self.package.get_record()

    def test_conference_tag(self):
        """Test for conference tag in 690C."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="690",
                                    ind1="C",
                                    code="a"),
            ["CONFERENCE", "CERN"]
        )

    def test_cnum(self):
        """Make sure that CNUM is okay."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="773",
                                    code="w"),
            ["C10-09-06.10"]
        )
        values = record_get_field_values(
            self.converted_record,
            tag="035",
            code="9"
        )
        self.assertTrue("INSPIRE-CNUM" in values)

    def test_date(self):
        """Test for proper date in 260."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="260",
                                    code="c"),
            ["2010"]
        )
        self.assertFalse(
            record_get_field_values(self.converted_record,
                                    tag="260",
                                    code="t")
        )


class TestINSPIRE2CDSConference(unittest.TestCase):

    """Test converted record data."""

    def setUp(self):
        """Load demo data."""
        from harvestingkit.bibrecord import BibRecordPackage
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        self.inspire_conf_demo_data_path = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_inspire_conf.xml')
        )

        bibrecs = BibRecordPackage(self.inspire_conf_demo_data_path)
        bibrecs.parse()
        self.parsed_record = bibrecs.get_records()[0]
        self.package = Inspire2CDS(self.parsed_record)
        self.recid = self.package.get_recid()
        self.converted_record = self.package.get_record()

    def test_conference_tag(self):
        """Test for conference tag in 690C."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="690",
                                    ind1="C",
                                    code="a"),
            ["CONFERENCE"]
        )

    def test_cnum(self):
        """Make sure that CNUM is okay."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="035",
                                    code="a",
                                    filter_subfield_code="9",
                                    filter_subfield_value="Inspire-CNUM"),
            ["C16-03-21.3"]
        )

    def test_date(self):
        """Test for proper date in 260."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="260",
                                    code="c"),
            ["2016"]
        )

    def test_collection(self):
        """Test for proper collection in 980."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="980",
                                    code="a"),
            ["ANNOUNCEMENT"]
        )

    def test_conference_info(self):
        """Test for proper info in 111."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="a"),
            ["Workshop on Topics in Three Dimensional Gravity"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="9"),
            ["20160321"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="f"),
            ["2016"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="c"),
            ["Miramare, Trieste, Italy"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="g"),
            ["miramare20160321"]
        )
        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="111",
                                    code="d"),
            ["21-24 Mar 2016"]
        )

    def test_conference_info_date_parsing(self):
        """Test conversion with the special cases for dates."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
          <datafield tag="111" ind1=" " ind2=" ">
            <subfield code="x">2016-03-21</subfield>
            <subfield code="y">2016-03-24</subfield>
            <subfield code="c">Somewhere, Someplace</subfield>
          </datafield>
          <datafield tag="111" ind1=" " ind2=" ">
            <subfield code="x">2016-03-30</subfield>
            <subfield code="y">2016-04-03</subfield>
            <subfield code="c">Somewhere</subfield>
          </datafield>
          <datafield tag="111" ind1=" " ind2=" ">
            <subfield code="x">2016-05-21</subfield>
            <subfield code="c">Someplace</subfield>
          </datafield>
          <datafield tag="111" ind1=" " ind2=" ">
            <subfield code="y">2016-03-21</subfield>
          </datafield>
          <datafield tag="111" ind1=" " ind2=" ">
            <subfield code="x">2016-03-24</subfield>
          </datafield>
          <datafield tag="980" ind1=" " ind2=" ">
            <subfield code="a">CONFERENCES</subfield>
          </datafield>
        </record>
        </collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()
            fields_111_d = record_get_field_values(converted_record,
                                                   tag="111",
                                                   code="d")

            assert len(fields_111_d) == 2
            assert '21-24 Mar 2016' in fields_111_d
            assert '30 Mar-03 Apr 2016' in fields_111_d


            fields_111_g = record_get_field_values(converted_record,
                                                   tag="111",
                                                   code="g")
            assert len(fields_111_g) == 3
            assert 'somewhere20160330' in fields_111_g
            assert 'somewhere20160321' in fields_111_g
            assert 'someplace20160521' in fields_111_g


class TestINSPIRE2CDSConferencePaper(unittest.TestCase):

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
        self.assertFalse(
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

        collections = record_get_field_values(
            self.converted_record,
            tag="980",
            code="a"
        )
        self.assertTrue("ConferencePaper" in collections)
        self.assertTrue("ARTICLE" in collections)
        self.assertTrue("PREPRINT" not in collections)

    def test_date(self):
        """Test for proper date in 260."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="260",
                                    code="c"),
            ["1997"]
        )

    def test_cern_tag(self):
        """Test for CERN tag in 690."""
        from harvestingkit.bibrecord import record_get_field_values

        self.assertEqual(
            record_get_field_values(self.converted_record,
                                    tag="690",
                                    ind1="C",
                                    code="a"),
            ["CERN"]
        )


class TestINSPIRE2CDSGeneric(unittest.TestCase):

    """Test specific conversions operations."""

    def test_experiments_conversion_with_leading_zero(self):
        """Test experiments conversion with removing leading zero."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
        <datafield tag="693" ind1=" " ind2=" ">
            <subfield code="e">CERN-RD-053</subfield>
        </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="693",
                                        code="a"),
                ["Not applicable"]
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="693",
                                        code="e"),
                ["RD53"]
            )

    def test_experiments_conversion_with_no_a(self):
        """Test experiments conversion with no $$a."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
        <datafield tag="693" ind1=" " ind2=" ">
            <subfield code="e">CERN-CAST</subfield>
        </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="693",
                                        code="a"),
                []
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="693",
                                        code="e"),
                ["CAST"]
            )

    def test_pubnote_conversion_with_pos_special_case(self):
        """Test pubnote conversion with the PoS special case for $p and $v."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
          <datafield tag="773" ind1=" " ind2=" ">
            <subfield code="c">018</subfield>
            <subfield code="p">PoS</subfield>
            <subfield code="v">QFTHEP2011</subfield>
            <subfield code="w">C11-09-24</subfield>
            <subfield code="y">2013</subfield>
          </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="773",
                                        code="p"),
                ["PoS"]
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="773",
                                        code="v"),
                ["QFTHEP2011"]
            )

    def test_author_conversion_with_no_v(self):
        """Test author conversion with the special case for $v."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
        <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">Mokhov, N.V.</subfield>
          <subfield code="v">Fermilab</subfield>
        </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="100",
                                        code="v"),
                []
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="100",
                                        code="a"),
                ["Mokhov, N V"]
            )

    def test_link_conversion_with_no_w(self):
        """Test link conversion with the special case for $w."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
          <datafield tag="856" ind1="4" ind2=" ">
            <subfield code="u">http://www.adsabs.harvard.edu/abs/1990NuPhS..13..535R</subfield>
            <subfield code="w">1990NuPhS..13..535R</subfield>
            <subfield code="y">ADSABS</subfield>
          </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="856",
                                        ind1="4",
                                        code="w"),
                []
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="856",
                                        ind1="4",
                                        code="u"),
                ["http://www.adsabs.harvard.edu/abs/1990NuPhS..13..535R"]
            )

    def test_thesis_conversion(self):
        """Test link conversion with the special case for $w."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
          <datafield tag="502" ind1=" " ind2=" ">
            <subfield code="b">Diploma</subfield>
            <subfield code="c">Freiburg U.</subfield>
            <subfield code="d">2005</subfield>
          </datafield>
          <datafield tag="980" ind1=" " ind2=" ">
            <subfield code="a">THESIS</subfield>
          </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="980",
                                        code="a"),
                ["THESIS"]
            )

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="502",
                                        code="a"),
                ["Diploma"]
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="502",
                                        code="b"),
                ["Freiburg U."]
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="502",
                                        code="c"),
                ["2005"]
            )

    def test_thesis_conversion_supervisors(self):
        """Test link conversion with the special case for $w."""
        from harvestingkit.bibrecord import record_get_field_values
        from harvestingkit.inspire_cds_package.from_inspire import Inspire2CDS

        xml = """<collection>
        <record>
          <datafield tag="701" ind1=" " ind2=" ">
            <subfield code="a">Besançon, Marc</subfield>
          </datafield>
          <datafield tag="701" ind1=" " ind2=" ">
            <subfield code="a">Ferri, Frederico</subfield>
          </datafield>
          <datafield tag="980" ind1=" " ind2=" ">
            <subfield code="a">THESIS</subfield>
          </datafield>
        </record></collection>
        """
        for record in Inspire2CDS.from_source(xml):
            converted_record = record.get_record()

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="980",
                                        code="a"),
                ["THESIS"]
            )

            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="700",
                                        code="a"),
                ["Besançon, Marc", "Ferri, Frederico"]
            )
            self.assertEqual(
                record_get_field_values(converted_record,
                                        tag="700",
                                        code="e"),
                ["dir.", "dir."]
            )


if __name__ == '__main__':
    unittest.main()
