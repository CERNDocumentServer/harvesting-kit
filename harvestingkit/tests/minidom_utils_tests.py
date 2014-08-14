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
from xml.dom.minidom import parseString
from harvestingkit.minidom_utils import (get_inner_xml,
                                         xml_to_text,
                                         get_value_in_tag,
                                         get_attribute_in_tag)

sample_xml = "<Foo>"\
             "  some text"\
             "  <Bar name=\"a\">Bar A</Bar>"\
             "  <Bar name=\"b\">Bar B</Bar>"\
             "</Foo>"


class MinidomUtilsTests(unittest.TestCase):

    def setUp(self):
        self.document = parseString(sample_xml)

    def test_get_inner_xml(self):
        tag = self.document.getElementsByTagName('Foo')[0]
        inner_xml = "some text"\
                    " <Bar name=\"a\">Bar A</Bar>"\
                    " <Bar name=\"b\">Bar B</Bar>"
        self.assertEqual(get_inner_xml(tag), inner_xml)
        self.assertEqual(get_inner_xml(self.document), sample_xml)

    def test_xml_to_text(self):
        self.assertEqual(xml_to_text(self.document), "some text Bar A Bar B")
        self.assertEqual(xml_to_text(self.document, delimiter=""), "some textBar ABar B")
        self.assertEqual(xml_to_text(self.document, delimiter="", tag_to_remove="Bar"), "some text")

    def test_get_value_in_tag(self):
        self.assertEqual(get_value_in_tag(self.document, "Bar"), "Bar A")
        self.assertEqual(get_value_in_tag(self.document, "A"), "")

    def test_get_attribute_in_tag(self):
        self.assertEqual(get_attribute_in_tag(self.document, "Bar", "name"), ["a", "b"])
        self.assertEqual(get_attribute_in_tag(self.document, "Bar", "A"), [])
        self.assertEqual(get_attribute_in_tag(self.document, "A", "Bar"), [])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(MinidomUtilsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
