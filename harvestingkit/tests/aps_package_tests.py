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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Harvesting Kit; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""Unit tests for APS."""

import unittest

from harvestingkit.aps_package import ApsPackage
from xml.dom.minidom import parse
from os.path import (join,
                     dirname)
from harvestingkit.tests import (__file__ as folder,
                                 aps_test_record,
                                 aps_output,
                                 journal_mappings)


class APSPackageTests(unittest.TestCase):

    """Test that metadata are exported correctly."""

    def setUp(self):
        """Setup sample parsing used in tests."""
        self.aps = ApsPackage(journal_mappings)
        self.aps.document = parse(join(dirname(folder), aps_test_record))

    def test_journal(self):
        """Test that journal name is extracted correctly."""
        self.assertEqual(self.aps._get_journal(), 'Phys. Rev. D')

    def test_abstract(self):
        """Test that abstract is extracted correctly."""
        abstract = '<p>In conformally flat background geometries the' \
                   ' long-wavelength gravitons can be described in the ' \
                   'fluid approximation and they induce scalar fluctuations ' \
                   'both during inflation and in the subsequent ' \
                   'radiation-dominated epoch. While this effect is minute ' \
                   'and suppressed for a de Sitter stage of expansion, the ' \
                   'fluctuations of the energy-momentum pseudotensor of the ' \
                   'graviton fluid lead to curvature perturbations that ' \
                   'increase with time all along the post-inflationary evolution.' \
                   ' An explicit calculation of these effects is presented for' \
                   ' a standard thermal history and it is shown that the growth' \
                   ' of the curvature perturbations caused by the long-wavelength ' \
                   'modes is approximately compensated by the slope of the power ' \
                   'spectra of the energy density, pressure and anisotropic ' \
                   'stress of the relic gravitons.</p>'
        self.assertEqual(self.aps._get_abstract(), abstract)

    def test_title(self):
        """Check that title is correct."""
        title = 'Scalar modes of the relic gravitons', '', []
        self.assertEqual(self.aps._get_title(), title)

    def test_doi(self):
        """Check that DOI is correct."""
        self.assertEqual(self.aps._get_doi(), '10.1103/PhysRevD.91.023521')

    def test_authors(self):
        """Check that authors are correct."""
        authors = [('Giovannini, Massimo', [u'a1'], [u'n1'])]
        self.assertEqual(self.aps._get_authors(), authors)

    def test_affiliations(self):
        """Check that affiliations are correct."""
        affiliations = {
            u'a1': 'Department of Physics, Theory Division, CERN , 1211 Geneva 23, Switzerland INFN, Section of Milan-Bicocca, 20126 Milan, Italy'
        }
        self.assertEqual(self.aps._get_affiliations(), affiliations)

    def test_author_emails(self):
        """Check email from author."""
        emails = {u'n1': ['massimo.giovannini@cern.ch']}
        self.assertEqual(self.aps._get_author_emails(), emails)

    def test_copyright(self):
        """Check that Copyright is extracted."""
        self.assertEqual(self.aps._get_copyright(), ('authors', '2015', 'Published by the American Physical Society'))

    def test_date(self):
        """Check published date."""
        self.assertEqual(self.aps._get_date(), '2015-01-29')

    def test_publisher(self):
        """Check correct publisher."""
        self.assertEqual(self.aps._get_publisher(), 'American Physical Society')

    def test_publication_information(self):
        """Check extracted pubinfo."""
        publication_information = ('Phys.Rev.',
                                   'D91',
                                   '2',
                                   u'2015',
                                   u'2015-01-29',
                                   u'10.1103/PhysRevD.91.023521',
                                   '023521',
                                   '',
                                   '')
        self.assertEqual(self.aps._get_publication_information(), publication_information)

    def test_pagecount(self):
        """Check pagecount."""
        self.assertEqual(self.aps._get_page_count(), '15')

    def test_pacscodes(self):
        """Check that PACS are extracted."""
        self.assertEqual(self.aps._get_pacscodes(), ['98.80.Cq', '04.30.-w', '04.62.+v', '98.70.Vc'])

    def test_subject(self):
        """Check subject."""
        self.assertEqual(self.aps._get_subject(), 'Cosmology')

    def test_license(self):
        """Check license."""
        self.assertEqual(
             self.aps._get_license(),
             ('Creative Commons Attribution 3.0 License',
              'creative-commons',
              'http://creativecommons.org/licenses/by/3.0/')
        )

    def test_keywords(self):
        """Check keywords."""
        self.assertEqual(self.aps._get_keywords(), [])

    def test_references(self):
        """Check references."""
        references = [
            (u'journal', '', [u'L.\u2009P. Grishchuk'], '', 'Zh.\xc3\x89ksp.Teor.Fiz.',
             '67', '825', '1974', '1', '', '', '', [], '', '', []),
            (u'journal', '', [u'L.\u2009P. Grishchuk'], '', 'Sov.Phys.JETP',
             '40', '409', '1975', '1', '', '', '', [], '', '', []),
            (u'journal', '10.1111/j.1749-6632.1977.tb37064.x', [u'L.\u2009P. Grishchuk'],
             '', 'Ann.N.Y.Acad.Sci.', '302', '439', '1977', '1', '', '', '', [], '', '', []),
            (u'journal', '10.1111/j.1749-6632.1977.tb37064.x', [u'L.\u2009P. Grishchuk'], '',
             'Ann.N.Y.Acad.Sci.', '302', '439', '1977', '1', '', '', '', [], '', '', []),
            (u'journal', '', [u'A.\u2009A. Starobinsky'], '', 'JETP Lett.',
             '30', '682', '1979', '2', '', '', '', [], '', '', []),
            (u'journal', '10.1016/0370-2693(82)90641-4', [u'V.\u2009A. Rubakov', u'M.\u2009V. Sazhin', u'A.\u2009V. Veryaskin'],
             '', 'Phys.Lett.', 'B115', '189', '1982', '2', '', '', '', [], '', '', []),
            (u'journal', '10.1016/0370-2693(83)91322-9', [u'R. Fabbri', u'M.\u2009D. Pollock'],
             '', 'Phys.Lett.', 'B125', '445', '1983', '3', '', '', '', [], '', '', []),
            (u'journal', '10.1016/0550-3213(84)90329-8', [u'L.\u2009F. Abbott', u'M.\u2009B. Wise'],
             '', 'Nucl.Phys.', '244', '541', '1984', '3', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.43.2566', [u'L.\u2009P. Grishchuk', u'M. Solokhin'], '',
             'Phys.Rev.', 'D43', '2566', '1991', '4', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.42.453', [u'V. Sahni'], '', 'Phys.Rev.',
             'D42', '453', '1990', '4', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.58.083504', [u'M. Giovannini'], '', 'Phys.Rev.',
             'D58', '083504', '1998', '5', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.60.123511', [u'M. Giovannini'], '', 'Phys.Rev.',
             'D60', '123511', '1999', '5', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0264-9381/26/4/045004', [u'M. Giovannini'], '',
             'Classical Quantum Gravity', '26', '045004', '2009', '5', '', '', '', [], '', '', []),
            (u'journal', '10.1016/j.physletb.2009.09.018', [u'W. Zhao', u'D. Baskaran', u'P. Coles'],
             '', 'Phys.Lett.', 'B680', '411', '2009', '5', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.80.042002', [u'M.\u2009S. Pshirkov', u'D. Baskaran'],
             '', 'Phys.Rev.', 'D80', '042002', '2009', '6', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.81.083503', [u'T. Chiba', u'K. Kamada', u'M. Yamaguchi'],
             '', 'Phys.Rev.', 'D81', '083503', '2010', '6', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.89.123513', [u'M.\u2009W. Hossain', u'R. Myrzakulov', u'M. Sami', u'E.\u2009N. Saridakis'],
             '', 'Phys.Rev.', 'D89', '123513', '2014', '6', '', '', '', [], '', '', []),
            (u'book', '', [u'C.\u2009W. Misner', u'K.\u2009S. Thorne', u'J.\u2009A. Wheeler'],
             '', 'Gravitation', '', '467', '1973', '7', '', 'Freeman', '', u'New York,', '', '', []),
            (u'book', '', [u'S. Weinberg'], '', 'Gravitation and Cosmology',
             '', '166', '1972', '8', '', 'Wiley', '', u'New York,', '', '', []),
            (u'book', '', [u'L.\u2009D. Landau', u'E.\u2009M. Lifshitz'], '',
             'The Classical Theory of Fields', '', '', '1971', '9', '', 'Pergamon Press', '', u'New York,', '', '', []),
            (u'journal', '10.1103/PhysRev.166.1263', [u'R. Isaacson'], '', 'Phys.Rev.', '166', '1263',
             '1968', '10', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRev.166.1272', [u'R. Isaacson'], '', 'Phys.Rev.', '166', '1272',
             '1968', '10', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.56.3248', [u'L.\u2009R. Abramo', u'R. Brandenberger', u'V. Mukahanov'],
             '', 'Phys.Rev.', 'D56', '3248', '1997', '11', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.60.064004', [u'L.\u2009R. Abramo'], '',
             'Phys Rev.', 'D60', '064004', '1999', '11', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.61.024038', [u'S.\u2009V. Babak', u'L.\u2009P. Grishchuk'],
             '', 'Phys.Rev.', 'D61', '024038', '1999', '11', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.73.083505', [u'M. Giovannini'], '',
             'Phys.Rev.', 'D73', '083505', '2006', '12', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.85.104012', [u'D. Su', u'Y. Zhang'],
             '', 'Phys.Rev.', 'D85', '104012', '2012', '12', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.16.1601', [u'L.\u2009H. Ford', u'L. Parker'],
             '', 'Phys.Rev.', 'D16', '1601', '1977', '13', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.16.245', [u'L.\u2009H. Ford', u'L. Parker'],
             '', 'Phys.Rev.', 'D16', '245', '1977', '13', '', '', '', [], '', '', []),
            (u'journal', '10.1016/0375-9601(77)90880-5', [u'B.\u2009L. Hu', u'L. Parker'],
             '', 'Phys.Lett', 'A63', '217', '1977', '13', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.22.1882', [u'J. Bardeen'], '',
             'Phys.Rev.', 'D22', '1882', '1980', '14', '', '', '', [], '', '', []),
            (u'journal', '10.1093/mnras/200.3.535', [u'G.\u2009V. Chibisov', u'V.\u2009F. Mukhanov'],
             '', 'Mon.Not.R.Astron.Soc.', '200', '535', '1982', '14', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.28.679', [u'J. Bardeen', u'P. Steinhardt', u'M. Turner'],
             '', 'Phys.Rev.', 'D28', '679', '1983', '14', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.30.265', [u'J.\u2009A. Frieman', u'M.\u2009S. Turner'],
             '', 'Phys.Rev.', 'D30', '265', '1984', '14', '', '', '', [], '', '', []),
            (u'journal', '10.1143/PTPS.78.1', [u'H. Kodama', u'M. Sasaki'], '',
             'Prog.Theor.Phys.Suppl.', '78', '1', '1984', '14', '', '', '', [], '', '', []),
            (u'journal', '10.1086/170206', [u'J-c. Hwang'], '',
             'Astrophys.J.', '375', '443', '1991', '14', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009N. Lukash'], '',
             'Zh.Eksp.Teor.Fiz.', '79', '1601', '1980', '15', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009N. Lukash'], '',
             'Sov.Phys.JETP', '52', '807', '1980', '15', '', '', '', [], '', '', []),
            (u'journal', '10.1134/S1063772907060017', [u'V. Strokov'],
             '', 'Astronomy Reports', '51', '431', '2007', '15', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0067-0049/192/2/15', [u'B. Gold'],
             '', 'Astrophys.J.Suppl.Ser.', '192', '15', '2011', '16', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0067-0049/192/2/16', [u'D. Larson'],
             '', 'Astrophys.J.Suppl.Ser.', '192', '16', '2011', '16', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0067-0049/192/2/17', [u'C.\u2009L. Bennett'],
             '', 'Astrophys.J.Suppl.Ser.', '192', '17', '2011', '16', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0067-0049/208/2/19', [u'G. Hinshaw'],
             '', 'Astrophys.J.Suppl.Ser.', '208', '19', '2013', '16', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0067-0049/208/2/20', [u'C.\u2009L. Bennett'],
             '', 'Astrophys.J.Suppl.Ser.', '208', '20', '2013', '16', '', '', '', [], '', '', []),
            (u'journal', '10.1086/377226', [u'D.\u2009N. Spergel'],
             '', 'Astrophys.J.Suppl.Ser.', '148', '175', '2003', '17', '', '', '', [], '', '', []),
            (u'journal', '10.1086/513700', [u'D.\u2009N. Spergel'],
             '', 'Astrophys.J.Suppl.Ser.', '170', '377', '2007', '17', '', '', '', [], '', '', []),
            (u'journal', '10.1086/513699', [u'L. Page'], '',
             'Astrophys.J.Suppl.Ser.', '170', '335', '2007', '17', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevLett.112.241101',
             [u'P.\u2009A.\u2009R. Ade'], 'BICEP2 Collaboration', 'Phys.Rev.Lett.', '112', '241101', '2014', '18', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0004-637X/792/1/62', [u'P.\u2009A.\u2009R. Ade'],
             'BICEP2 Collaboration', 'Astrophys.J.', '792', '62', '2014', '18', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.8.4231', [u'G.\u2009L. Murphy'],
             '', 'Phys.Rev.', 'D8', '4231', '1973', '19', '', '', '', [], '', '', []),
            (u'journal', '10.1016/0375-9601(77)90953-7', [u'G.\u2009L. Murphy'],
             '', 'Phys.Lett.', 'A62', '75', '1977', '19', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009A. Belinskii', u'I.\u2009M. Khalatnikov'],
             '', 'Zh.Eksp.Teor.Fiz.', '69', '401', '1975', '20', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009A. Belinskii', u'I.\u2009M. Khalatnikov'],
             '', 'Sov.Phys.JETP', '42', '205', '1976', '20', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009A. Belinskii', u'I.\u2009M. Khalatnikov'],
             '', 'Zh.Eksp.Teor.Fiz.Pis.Red.', '21', '223', '1975', '20', '', '', '', [], '', '', []),
            (u'journal', '', [u'V.\u2009A. Belinskii', u'I.\u2009M. Khalatnikov'],
             '', 'JETP Lett.', '21', '99', '1975', '20', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.72.043514', [u'S. Weinberg'],
             '', 'Phys.Rev.', 'D72', '043514', '2005', '21', '', '', '', [], '', '', []),
            (u'journal', '10.1103/PhysRevD.74.023508', [u'S. Weinberg'],
             '', 'Phys.Rev.', 'D74', '023508', '2006', '21', '', '', '', [], '', '', []),
            (u'journal', '10.1088/0305-4470/35/5/312', [u'A. Romeo', u'A.A. Saharian'],
             '', 'J.Phys.', 'A35', '1297', '2002', '22', '', '', '', [], '', '', []),
            (u'book', '', [u'A.A. Saharian'], '', 
             'The Generalized Abel-Plana Formula with Applications to Bessel Functions and Casimir Effect', 
             '', '', '2008', '22', '', 
             'Yerevan State University Publishing House', '', u'Yerevan,', '', '', []),
            (u'report', '', [u'A. Romeo', u'A.A. Saharian'], 
             '', '', '', '', '', '22', '', '', '', u'Report No ICTP/2007/082', '', '', [])
        ]
        for ref in self.aps.document.getElementsByTagName('ref'):
            for innerref in self.aps._get_reference(ref):
                self.assertTrue(innerref in references)
    def test_article_type(self):
        """Check extracted article type."""
        self.assertEqual(self.aps._get_article_type(), 'research-article')

    def test_get_record(self):
        """Check full record conversion."""
        source_file = join(dirname(folder), aps_test_record)
        marc_file = join(dirname(folder), aps_output)
        with open(marc_file) as marc:
            result = marc.read()
        xml = self.aps.get_record(source_file)
        self.assertEqual(xml.strip(), result.strip())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(APSPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
