## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Testing module for SCOAP3 harvests"""

import unittest

from invenio.testutils import make_test_suite, run_test_suite

## Tests need to work for harvesting Elsevier and Springer
class TestArxivIds(unittest.TestCase):
    """Test arXiv IDs"""

    def test_arxiv_ids_are_extracted(self):
        pass

    def test_record_has_correctly_added_arxiv_id(self):
        pass


class TestMathMl(unittest.TestCase):
    """Test MathML support."""

    def test_mathml_has_namespace_correctly_changed(self):
        pass

    def test_mathml_is_added_to_title(self):
        pass

    def test_mathml_is_added_to_abstract(self):
        pass

    def test_mathml_is_added_to_keywords(self):
        pass


class TestPackages(unittest.TestCase):
    """Test packages harvest, extraction, normalization."""

    def test_packages_were_harvested(self):
        pass

    def test_package_was_extracted(self):
        pass

    def test_package_was_normalized(self):
        pass

class TestRecordCreation(unittest.TestCase):
    """Test the creation of bibrecord."""

    def test_record_created(self):
        pass


TEST_SUITE = make_test_suite(TestArxivIds,
                             TestMathMl,
                             TestPackages,
                             TestRecordCreation)

if __name__ == "__main__":

    run_test_suite(TEST_SUITE)
