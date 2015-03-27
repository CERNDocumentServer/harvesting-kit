# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014 CERN.
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

"""Tests for the PosPackage."""

import unittest
import pkg_resources
import os

from xml.dom.minidom import parse

from harvestingkit.pos_package import PosPackage


class POSPackageTests(unittest.TestCase):

    """Tests for the PosPackage."""

    def setUp(self):
        """Setup test."""
        self.pos = PosPackage()
        sample_filepath = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_pos_record.xml')
        )
        self.pos.document = parse(sample_filepath)

    def test_authors(self):
        """Test the field authors."""
        self.assertEqual(self.pos._get_authors(),
                         [('El-Khadra, Aida', ['INFN and Università di Firenze'])])

    def test_language(self):
        """Test the field language."""
        self.assertEqual(self.pos._get_language(), 'en')

    def test_publisher(self):
        """Test the field publisher."""
        self.assertEqual(self.pos._get_publisher(), 'SISSA')

    def test_date(self):
        """Test the field date."""
        self.assertEqual(self.pos._get_date(), '2014-03-19')

    def test_title(self):
        """Test the field title."""
        self.assertEqual(self.pos._get_title(), 'Heavy Flavour Physics Review')

    def test_copyright(self):
        """Test the field copyright."""
        self.assertEqual(self.pos._get_copyright(), 'CC-BY-NC-SA')

    def test_subject(self):
        """Test the field subject."""
        self.assertEqual(self.pos._get_subject(), 'Lattice Field Theory')

    def test_identifier(self):
        """Test the field identifier."""
        self.assertEqual(self.pos.get_identifier(), 'oai:pos.sissa.it:LATTICE 2013/001')

    def test_record(self):
        """Test the field identifier."""
        record = self.pos.get_record(self.pos.document)
        self.assertTrue(record["100"])
        self.assertTrue(record["980"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(POSPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
