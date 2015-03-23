# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014, 2015 CERN.
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

import unittest

from harvestingkit.html_utils import MathMLParser


class HTMLUtilsTests(unittest.TestCase):

    """Tests for all utility functions."""

    def test_mathml(self):
        """Test that MathML is kept."""
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
        self.assertEqual(MathMLParser.html_to_text(data), data)

    def test_html(self):
        """Test that HTML is stripped."""
        data = (u'<p><roman>CH</roman><sub>3</sub><roman>NH</roman><sub>3</sub>'
                u'<roman>PbX</roman>(<roman>X</roman> = <roman>Br</roman>, '
                u'<roman>I</roman>, <roman>Cl</roman>) perovskites have recently'
                u'been used as light absorbers in hybrid organic-inorganic solid-state'
                u' solar cells, with efficiencies above 15%.</p>')
        expected_data = (u'CH3NH3PbX(X = Br, I, Cl) perovskites have recently'
                         u'been used as light absorbers in hybrid organic-inorganic solid-state '
                         u'solar cells, with efficiencies above 15%.')
        self.assertEqual(MathMLParser.html_to_text(data), expected_data)

    def test_htmlentity(self):
        """Test that HTML entities are kept."""
        data = "This &amp; that and &lt; is there."
        self.assertEqual(MathMLParser.html_to_text(data), data)

    def test_xml_encoding(self):
        """Test that HTML entities are kept."""
        data = "This & that and 2<y<3 is > there."
        expected_data = "This &amp; that and 2&lt;y&lt;3 is > there."
        self.assertEqual(MathMLParser.html_to_text(data), expected_data)

    def test_htmlentity_case(self):
        """Test that HTML entities are dealt with smartly."""
        data = (u'Project at CERN, Proc. of the Workshop on Future Directions in Detector R&D;')
        expected_data = (u'Project at CERN, Proc. of the Workshop on Future Directions in Detector R&amp;D;')
        self.assertEqual(MathMLParser.html_to_text(data), expected_data)

if __name__ == '__main__':
    unittest.main()
