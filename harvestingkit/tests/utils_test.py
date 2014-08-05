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
from harvestingkit.utils import (format_arxiv_id,
                                 collapse_initials,
                                 fix_journal_name)
from harvestingkit.tests import journal_mappings


class UtilsTests(unittest.TestCase):
    def test_format_arxiv_id(self):
        self.assertEqual(format_arxiv_id("arXiv:1312.1300"), "arXiv:1312.1300")
        self.assertEqual(format_arxiv_id("1312.1300"), "arXiv:1312.1300")
        self.assertEqual(format_arxiv_id("arxiv:hep/1312/1300", True), "hep/1312/1300")
        self.assertEqual(format_arxiv_id("arxiv:hep/1312/1300"), "arxiv:hep/1312/1300")

    def test_collapse_initials(self):
        self.assertEqual(collapse_initials("T. A. Adams"), "T.A. Adams")
        self.assertEqual(collapse_initials("T.   A. Adams"), "T.A. Adams")
        self.assertEqual(collapse_initials("T. A. V. Adams"), "T.A.V. Adams")

    def test_fix_journal_name(self):
        self.assertEqual(fix_journal_name("A&A", journal_mappings), ('Astron.Astrophys.', ""))
        self.assertEqual(fix_journal_name("A&A B", journal_mappings), ('Astron.Astrophys.', "B"))
        self.assertEqual(fix_journal_name("A&A.B", journal_mappings), ('A&A.', "B"))
        self.assertEqual(fix_journal_name("A&AB.", journal_mappings), ("A&AB.", ""))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(UtilsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
