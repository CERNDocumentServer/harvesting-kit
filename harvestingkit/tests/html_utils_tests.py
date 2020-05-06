# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2014, 2015, 2020 CERN.
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

    def test_mathml_mml(self):
        """Test that MathML with mml namespace prefix is handled."""
        abstract = u"""<p>The determination of the Higgs self-coupling is one of the key ingredients for understanding the mechanism behind the electroweak symmetry breaking. An indirect method for constraining the Higgs trilinear self-coupling via single Higgs production at next-to-leading order (NLO) has been proposed in order to avoid the drawbacks of studies with double Higgs production. In this paper we study the Higgs self-interaction through the vector boson fusion (VBF) process <inline-formula><mml:math display="inline"><mml:msup><mml:mi>e</mml:mi><mml:mo>-</mml:mo></mml:msup><mml:mi>p</mml:mi><mml:mo stretchy="false">\u2192</mml:mo><mml:msub><mml:mi>\u03bd</mml:mi><mml:mi>e</mml:mi></mml:msub><mml:mi>h</mml:mi><mml:mi>j</mml:mi></mml:math></inline-formula> at the future LHeC. At NLO level, we compute analytically the scattering amplitudes for relevant processes, in particular those induced by the Higgs self-interaction. A Monte\xa0Carlo simulation and a statistical analysis utilizing the analytic results are then carried out for Higgs production through VBF and decay to <inline-formula><mml:math display="inline"><mml:mi>b</mml:mi><mml:mover accent="true"><mml:mi>b</mml:mi><mml:mo stretchy="false">\xaf</mml:mo></mml:mover></mml:math></inline-formula>, which yield for the trilinear Higgs self-coupling rescaling parameter <inline-formula><mml:math display="inline"><mml:msub><mml:mi>\u03ba</mml:mi><mml:mi>\u03bb</mml:mi></mml:msub></mml:math></inline-formula> the limit [<inline-formula><mml:math display="inline"><mml:mrow><mml:mo>-</mml:mo><mml:mn>0.57</mml:mn></mml:mrow></mml:math></inline-formula>, 2.98] with <inline-formula><mml:math display="inline"><mml:mn>2</mml:mn><mml:mtext>\u2009</mml:mtext><mml:mtext>\u2009</mml:mtext><mml:msup><mml:mi>ab</mml:mi><mml:mrow><mml:mo>-</mml:mo><mml:mn>1</mml:mn></mml:mrow></mml:msup></mml:math></inline-formula> integrated luminosity. If we assume about 10% of the signal survives the event selection cuts, and include all the background, the constraint will be broadened to [<inline-formula><mml:math display="inline"><mml:mrow><mml:mo>-</mml:mo><mml:mn>2.11</mml:mn></mml:mrow></mml:math></inline-formula>, 4.63].</p>"""
        expected = u"""The determination of the Higgs self-coupling is one of the key ingredients for understanding the mechanism behind the electroweak symmetry breaking. An indirect method for constraining the Higgs trilinear self-coupling via single Higgs production at next-to-leading order (NLO) has been proposed in order to avoid the drawbacks of studies with double Higgs production. In this paper we study the Higgs self-interaction through the vector boson fusion (VBF) process <math display="inline"><msup><mi>e</mi><mo>-</mo></msup><mi>p</mi><mo stretchy="false">\u2192</mo><msub><mi>\u03bd</mi><mi>e</mi></msub><mi>h</mi><mi>j</mi></math> at the future LHeC. At NLO level, we compute analytically the scattering amplitudes for relevant processes, in particular those induced by the Higgs self-interaction. A Monte\xa0Carlo simulation and a statistical analysis utilizing the analytic results are then carried out for Higgs production through VBF and decay to <math display="inline"><mi>b</mi><mover accent="true"><mi>b</mi><mo stretchy="false">\xaf</mo></mover></math>, which yield for the trilinear Higgs self-coupling rescaling parameter <math display="inline"><msub><mi>\u03ba</mi><mi>\u03bb</mi></msub></math> the limit [<math display="inline"><mrow><mo>-</mo><mn>0.57</mn></mrow></math>, 2.98] with <math display="inline"><mn>2</mn><mtext>\u2009</mtext><mtext>\u2009</mtext><msup><mi>ab</mi><mrow><mo>-</mo><mn>1</mn></mrow></msup></math> integrated luminosity. If we assume about 10% of the signal survives the event selection cuts, and include all the background, the constraint will be broadened to [<math display="inline"><mrow><mo>-</mo><mn>2.11</mn></mrow></math>, 4.63]."""
        self.assertEqual(MathMLParser.html_to_text(abstract), expected)

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
        data = "This & that and 2&lt;y&lt;3 is > there."
        expected_data = "This &amp; that and 2&lt;y&lt;3 is > there."
        self.assertEqual(MathMLParser.html_to_text(data), expected_data)

    def test_htmlentity_case(self):
        """Test that HTML entities are dealt with smartly."""
        data = (u'Project at CERN, Proc. of the Workshop on Future Directions in Detector R&D;')
        expected_data = (u'Project at CERN, Proc. of the Workshop on Future Directions in Detector R&amp;D;')
        self.assertEqual(MathMLParser.html_to_text(data), expected_data)

if __name__ == '__main__':
    unittest.main()
