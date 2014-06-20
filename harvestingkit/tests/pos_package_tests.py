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
import unittest
from harvestingkit.pos_package import PosPackage
from xml.dom.minidom import parse
from os.path import (join,
                     dirname)
from harvestingkit.tests import (__file__ as folder,
                                 pos_test_record)


class POSPackageTests(unittest.TestCase):
    def setUp(self):
        self.pos = PosPackage()
        self.pos.document = parse(join(dirname(folder), pos_test_record))

    def test_authors(self):
        self.assertEqual(self.pos._get_authors(), ['El-Khadra, Aida', 'Johnson, A.T.'])

    def test_language(self):
        self.assertEqual(self.pos._get_language(), 'en')

    def test_publisher(self):
        self.assertEqual(self.pos._get_publisher(), 'SISSA')

    def test_date(self):
        self.assertEqual(self.pos._get_date(), '2014-03-19')

    def test_copyright(self):
        self.assertEqual(self.pos._get_copyright(), 'CC-BY-NC-SA')

    def test_subject(self):
        self.assertEqual(self.pos._get_subject(), 'Lattice Field Theory')

    def test_identifier(self):
        self.assertEqual(self.pos.get_identifier(), 'oai:pos.sissa.it:LATTICE 2013/001')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(POSPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
