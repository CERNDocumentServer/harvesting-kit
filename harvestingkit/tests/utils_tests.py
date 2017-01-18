# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014, 2015, 2017 CERN.
#
# Harvesting Kit is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Harvesting Kit is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import os
import unittest
import httpretty
import tempfile
import pkg_resources

from harvestingkit.utils import (record_add_field,
                                 create_record,
                                 format_arxiv_id,
                                 collapse_initials,
                                 fix_journal_name,
                                 escape_for_xml,
                                 fix_dashes,
                                 download_file,
                                 run_shell_command,
                                 record_xml_output,
                                 fix_title_capitalization,
                                 return_letters_from_string,
                                 convert_html_subscripts_to_latex,
                                 safe_title,
                                 license_is_oa,
                                 make_user_agent)
from harvestingkit.tests import journal_mappings


class UtilsTests(unittest.TestCase):

    """Tests for all utility functions."""

    def test_record_add_field(self):
        """Test adding field to record."""
        data = (u'In this paper we continue the study of Q -operators in'
                u' the six-vertex model and its higher spin generalizations.'
                u' In [1] we derived a new expression for the higher spin R'
                u' -matrix associated with the affine quantum algebra '
                u'<math xmlns="http://www.w3.org/1998/Math/MathML" altimg="si1.gif">'
                u'<msub><mrow><mi>U</mi></mrow><mrow><mi>q</mi></mrow></msub>'
                u'<mo stretchy="false">(</mo><mover accent="true"><mrow><mrow>'
                u'<mi mathvariant="italic">sl</mi></mrow><mo stretchy="false">'
                u'(</mo><mn>2</mn><mo stretchy="false">)</mo></mrow><mrow><mo>'
                u'^</mo></mrow></mover><mo stretchy="false">)</mo></math>'
                u' . Taking a special limit in this R -matrix we obtained new'
                u' formulas for the Q -operators acting in the tensor product'
                u' of representation spaces with arbitrary complex spin.')
        rec = create_record()
        record_add_field(rec, '520', subfields=[('a', data)])
        data = (u"<record><datafield ind1=\"\" ind2=\"\" tag=\"520\">"
                u"<subfield code=\"a\">") + data
        data += u"</subfield></datafield></record>"
        self.assertEqual(record_xml_output(rec, pretty=False), data)

    def test_record_add_field_fallback(self):
        """Test adding field with special data to record."""
        rec = create_record()
        record_add_field(rec, "035", subfields=[('a', "<arXiv:1234.1242>")])
        data = (u"<record><datafield ind1=\"\" ind2=\"\" tag=\"035\">"
                u"<subfield code=\"a\">"
                u"&lt;arXiv:1234.1242></subfield></datafield></record>")
        self.assertEqual(record_xml_output(rec, pretty=False), data)

    def test_record_add_field_with_special_content(self):
        """Test adding field with special data to record."""
        rec = create_record()
        record_add_field(rec, "035", subfields=[('a', "4.0<as 123")])
        data = (u"<record><datafield ind1=\"\" ind2=\"\" tag=\"035\">"
                u"<subfield code=\"a\">"
                u"4.0&lt;as 123</subfield></datafield></record>")
        self.assertEqual(record_xml_output(rec, pretty=False), data)

    def test_format_arxiv_id(self):
        """Test arXiv formatting."""
        self.assertEqual(format_arxiv_id("arXiv:1312.1300"), "arXiv:1312.1300")
        self.assertEqual(format_arxiv_id("1312.1300"), "arXiv:1312.1300")
        self.assertEqual(format_arxiv_id("1312.13005"), "arXiv:1312.13005")
        self.assertEqual(format_arxiv_id("arxiv:hep/1312002"), "hep/1312002")
        self.assertEqual(format_arxiv_id("hep/1312002"), "hep/1312002")
        self.assertEqual(format_arxiv_id("arXiv:1234.12345"), "arXiv:1234.12345")

    def test_collapse_initials(self):
        """Test proper initial handling."""
        self.assertEqual(collapse_initials("T. A. Adams"), "T.A. Adams")
        self.assertEqual(collapse_initials("T.-A. Adams"), "T.A. Adams")
        self.assertEqual(collapse_initials("T.   A. Adams"), "T.A. Adams")
        self.assertEqual(collapse_initials("T. A."), "T.A.")
        self.assertEqual(collapse_initials("T. A. V. Adams"), "T.A.V. Adams")

    def test_fix_journal_name(self):
        """Test journal name handling."""
        self.assertEqual(fix_journal_name("A&A", journal_mappings), ('Astron.Astrophys.', ""))
        self.assertEqual(fix_journal_name("A&A B", journal_mappings), ('Astron.Astrophys.', "B"))
        self.assertEqual(fix_journal_name("A&A.B", journal_mappings), ('A&A.', "B"))
        self.assertEqual(fix_journal_name("A&AB.", journal_mappings), ("A&AB.", ""))

    def test_safe_title(self):
        """Test journal name handling."""
        self.assertEqual(safe_title("García"), "García")
        self.assertEqual(safe_title("a garcía"), "A García")
        self.assertEqual(safe_title("THIS IS A LONG"), "This Is A Long")

    def test_escape_ampersand(self):
        """Test ampersand handling."""
        self.assertEqual(escape_for_xml("A&A"), "A&amp;A")
        self.assertEqual(escape_for_xml("asdasdsa 2.2<y<3.4 A"), "asdasdsa 2.2&lt;y&lt;3.4 A")
        self.assertEqual(escape_for_xml("range -4.0< @h<-2.5"), "range -4.0&lt; @h&lt;-2.5")
        # happens if not unescaped..
        self.assertEqual(escape_for_xml("A &amp; A.B"), "A &amp;amp; A.B")

        longtext = "range 2.7<y<3.8, are presented, <p_T^2> with"
        self.assertEqual(
            escape_for_xml(longtext),
            "range 2.7&lt;y&lt;3.8, are presented, &lt;p_T^2> with"
        )

        from harvestingkit.html_utils import MathMLParser

        keep_existing = "for 0.03&lt;x&lt;0.1 and fit to world data"
        self.assertEqual(escape_for_xml(MathMLParser().unescape(keep_existing)), keep_existing)
        self.assertEqual(escape_for_xml(MathMLParser().unescape("A&amp;A & B")), "A&amp;A &amp; B")
        self.assertEqual(
            escape_for_xml("ont essayé à<ll' pliquer",
                           tags_to_keep=MathMLParser.mathml_elements),
            "ont essayé à&lt;ll' pliquer"
        )

    def test_fix_dashes(self):
        """Test dashes."""
        self.assertEqual(fix_dashes(u"A–A"), "A-A")
        self.assertEqual(fix_dashes(u'-–'), '-')
        self.assertEqual(fix_dashes(u'––'), '-')
        self.assertEqual(fix_dashes(u'–––'), '-')

    def test_html_latex_subscripts(self):
        """Test dashes."""
        data = (u'In this paper we continue the study of Q -operators in'
                u' the six-vertex model <roman><sub>3</sub>M</roman>.'
                u' In [1] <sup>2</sup>x new expression for the higher spin R')
        expected_data = (
            u'In this paper we continue the study of Q -operators in'
            u' the six-vertex model <roman>$_{3}$M</roman>.'
            u' In [1] $^{2}$x new expression for the higher spin R'
        )

        self.assertEqual(
            convert_html_subscripts_to_latex(data), expected_data
        )

    def test_fix_title_capitalization(self):
        """Test title capitalization."""
        self.assertEqual(fix_title_capitalization(u"A TITLE"), "A Title")
        self.assertEqual(fix_title_capitalization(u"a title"), "A Title")
        self.assertEqual(fix_title_capitalization(u"A TITLE LHC IS"), "A Title LHC is")
        self.assertEqual(fix_title_capitalization(u"A title LHC is"), "A title LHC is")

    @httpretty.activate
    def test_download_file(self):
        """Test if download_file works."""
        httpretty.register_uri(
            httpretty.GET,
            "http://example.com/test.txt",
            body="Lorem ipsum\n",
            status=200
        )
        file_fd, file_name = tempfile.mkstemp()
        os.close(file_fd)
        download_file("http://example.com/test.txt", file_name)
        self.assertEqual("Lorem ipsum\n", open(file_name).read())

    def test_run_shell(self):
        """Test if run_shell_command works."""
        code, out, err = run_shell_command(['echo', 'hello world'])
        self.assertEqual(out, "hello world\n")

    def test_run_shell_for_xmllint(self):
        """Test if run_shell_command works for xmllint."""
        xmllint_resources = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'si520')
        )
        xmllint = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_issue', 'issue.xml')
        )
        xmllint_output = pkg_resources.resource_string(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_issue', 'resolved_issue.xml')
        )

        command = ['xmllint',
                   '--format',
                   '--path',
                   xmllint_resources,
                   '--loaddtd',
                   xmllint]
        code, out, err = run_shell_command(command)
        self.assertEqual(out, xmllint_output)

    def test_run_shell_for_xmllint_with_dtd540(self):
        """Test if run_shell_command works for xmllint."""
        xmllint_resources = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'si540')
        )
        xmllint = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_540_issue', 'issue.xml')
        )
        xmllint_output = pkg_resources.resource_string(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_540_issue', 'resolved_issue.xml')
        )

        command = ['xmllint',
                   '--format',
                   '--path',
                   xmllint_resources,
                   '--loaddtd',
                   xmllint]
        code, out, err = run_shell_command(command)
        self.assertEqual(out, xmllint_output)

    def test_letters_from_string(self):
        """Test that only letters are returned."""
        self.assertEqual(
            return_letters_from_string("65B"), "B"
        )
        self.assertEqual(
            return_letters_from_string("65"), ""
        )
        self.assertEqual(
            return_letters_from_string("6sdf5"), "sdf"
        )
        self.assertEqual(
            return_letters_from_string("sas24ss"), "sasss"
        )
        self.assertEqual(
            return_letters_from_string("sasss"), "sasss"
        )

    def test_license_is_oa(self):
        """Test OA from license determination."""
        self.assertEqual(license_is_oa("OA"), True)
        self.assertEqual(license_is_oa("CC-BY-NC 2.0"), True)
        self.assertEqual(
            license_is_oa("http://creativecommons.org/licenses/by-nc/3.0/"),
            True
        )
        self.assertEqual(license_is_oa("APS"), False)
        self.assertEqual(license_is_oa("not OA"), False)


    def test_make_user_agent(self):
        """Test User-Agent string from package info."""
        self.assertIn('HarvestingKit/', make_user_agent(), 'test UA product')
        self.assertIn(' Elsevier', make_user_agent('Elsevier'), 'test UA component')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(UtilsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
