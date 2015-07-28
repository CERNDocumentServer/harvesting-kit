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

"""Tests for Elsevier."""

import os
import unittest
import pkg_resources

from harvestingkit.elsevier_package import ElsevierPackage
from xml.dom.minidom import parse, parseString, Element
from harvestingkit.tests import journal_mappings


class ElsevierScoap3PackageTests(unittest.TestCase):

    """Test extraction of Elsevier records in SCOAP3."""

    def setUp(self):
        """Setup initial document."""
        self.els = ElsevierPackage(no_harvest=True)
        self.document = parse(pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_document_output.xml')
        ))
        self.document540 = parse(pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_540_document_output.xml')
        ))

    ## tests for documents
    def test_doi(self):
         """Test that doi is good."""
         self.assertEqual(self.els._get_doi(self.document), '10.1016/j.nuclphysb.2015.07.011')

    def test_540_doi(self):
         """Test that doi is good."""
         self.assertEqual(self.els._get_doi(self.document540), '10.1016/j.cell.2015.03.041')

    def test_title(self):
        """Test that title is good."""
        self.assertEqual(self.els.get_title(self.document), 'F-theory vacua with <math altimg="si1.gif" xmlns="http://www.w3.org/1998/Math/MathML"><msub><mrow><mi mathvariant="double-struck">Z</mi></mrow><mrow><mn>3</mn></mrow></msub></math> gauge symmetry')

    def test_540_title(self):
        """Test that title is good."""
        self.assertEqual(self.els.get_title(self.document540), 'Bending Gradients: How the Intestinal Stem Cell Gets Its Home')

    def test_doctype(self):
        """Test that doctype is good."""
        self.assertEqual(self.els.get_doctype(self.document), '')

    def test_540_doctype(self):
        """Test that doctype is good."""
        self.assertEqual(self.els.get_doctype(self.document540), '')

    def test_abstract(self):
        """Test that abstract is good."""
        abstract = 'Discrete gauge groups naturally arise in F-theory compactifications on genus-one fibered '\
                   'Calabi\xe2\x80\x93Yau manifolds. Such geometries appear in families that are parameterized '\
                   'by the Tate\xe2\x80\x93Shafarevich group of the genus-one fibration. While the F-theory '\
                   'compactification on any element of this family gives rise to the same physics, the corresponding '\
                   'M-theory compactifications on these geometries differ and are obtained by a fluxed circle '\
                   'reduction of the former. In this note, we focus on an element of order three in the '\
                   'Tate\xe2\x80\x93Shafarevich group of the general cubic. We discuss how the different M-theory '\
                   'vacua and the associated discrete gauge groups can be obtained by Higgsing of a pair of '\
                   'five-dimensional U(1) symmetries. The Higgs fields arise from vanishing cycles in '\
                   '<math altimg="si2.gif" xmlns="http://www.w3.org/1998/Math/MathML"><msub><mrow><mi>I</mi></mrow>'\
                   '<mrow><mn>2</mn></mrow></msub></math> -fibers that appear at certain codimension two loci in the '\
                   'base. We explicitly identify all three curves that give rise to the corresponding Higgs fields. '\
                   'In this analysis the investigation of different resolved phases of the underlying geometry plays '\
                   'a crucial r\xc3\xb4le.'

        self.assertEqual(self.els.get_abstract(self.document), abstract)

    def test_540_abstract(self):
        """Test that abstract is good."""
        abstract = 'We address the mechanism by which adult intestinal stem cells (ISCs) become localized to the '\
                   'base of each villus during embryonic development. We find that, early in gut development, '\
                   'proliferating progenitors expressing ISC markers are evenly distributed throughout the '\
                   'epithelium, in both the chick and mouse. However, as the villi form, the putative stem cells '\
                   'become restricted to the base of the villi. This shift in the localization is driven by '\
                   'mechanically influenced reciprocal signaling between the epithelium and underlying mesenchyme. '\
                   'Buckling forces physically distort the shape of the morphogenic field, causing local maxima of '\
                   'epithelial signals, in particular Shh, at the tip of each villus. This induces a suite\xc2\xa0of '\
                   'high-threshold response genes in the underlying mesenchyme to form a signaling center called '\
                   'the\xc2\xa0\xe2\x80\x9cvillus cluster.\xe2\x80\x9d Villus cluster signals, notably Bmp4, feed '\
                   'back on the overlying epithelium to ultimately restrict the stem cells to the base of each villus.'

        self.assertEqual(self.els.get_abstract(self.document540), abstract)

    def test_keywords(self):
        """Test that keywords are good."""
        keywords = []
        self.assertEqual(self.els.get_keywords(self.document), keywords)

    def test_540_keywords(self):
        """Test that keywords are good."""
        keywords = []
        self.assertEqual(self.els.get_keywords(self.document540), keywords)

    def test_add_orcids(self):
        """Test that orcids are good.

        According to "Tag by Tag The Elsevier DTD 5 Family of XML DTDs" orcids will be
        distributed as an attribute in the ce:author tag.
        """
        xml_author = Element('ce:author')
        xml_author.setAttribute('orcid', '1234-5678-4321-8765')
        authors = [{}]

        # _add_orcids will alter the authors list
        self.els._add_orcids(authors, [xml_author])

        self.assertEqual(authors, [{'orcid': 'ORCID:1234-5678-4321-8765'}])

    def test_authors(self):
        """Test that authors are good."""
        authors = [{'affiliation': ['Department of Physics and Astronomy, University of Pennsylvania, Philadelphia, PA, 19104-6396, USA'],
                    'cross_ref': ['aff0010'],
                    'surname': 'Cveti\xc4\x8d',
                    'given_name': 'Mirjam',
                    'email': 'cvetic@cvetic.hep.upenn.edu'},
                   {'affiliation': ['Department of Physics and Astronomy, University of Pennsylvania, Philadelphia, PA, 19104-6396, USA',
                                    'Department of Mathematics, University of Pennsylvania, Philadelphia, PA, 19104-6396, USA'],
                    'cross_ref': ['aff0010', 'aff0020', 'cr0010'],
                    'surname': 'Donagi',
                    'given_name': 'Ron',
                    'email': 'donagi@math.upenn.edu'},
                   {'affiliation': ['Theory Group, Physics Department, CERN, Geneva 23, CH-1211, Switzerland'], 'cross_ref': ['aff0030'], 'surname': 'Klevers', 'given_name': 'Denis', 'email': 'Denis.Klevers@cern.ch'},
                   {'affiliation': ['Department of Physics and Astronomy, University of Pennsylvania, Philadelphia, PA, 19104-6396, USA'], 'cross_ref': ['aff0010'], 'surname': 'Piragua', 'given_name': 'Hernan', 'email': 'hpiragua@sas.upenn.edu'},
                   {'affiliation': ['Department of Physics and Astronomy, University of Pennsylvania, Philadelphia, PA, 19104-6396, USA'], 'cross_ref': ['aff0010'], 'surname': 'Poretschkin', 'given_name': 'Maximilian', 'email': 'mporet@sas.upenn.edu'}]
        self.assertEqual(self.els.get_authors(self.document), authors)

    def test_540_authors(self):
        """Test that authors are good."""
        authors = [{'affiliation': ['Department of Genetics, Harvard Medical School, Boston, MA 02115, USA'],
                    'surname': 'Shyer',
                    'given_name': 'Amy\xc2\xa0E.',
                    'cross_ref': ['aff1', 'fn1']},
                   {'affiliation': ['Department of Genetics, Harvard Medical School, Boston, MA 02115, USA'], 'surname': 'Huycke', 'given_name': 'Tyler\xc2\xa0R.', 'cross_ref': ['aff1']},
                   {'affiliation': ['Department of Genetics, Harvard Medical School, Boston, MA 02115, USA'], 'surname': 'Lee', 'given_name': 'ChangHee', 'cross_ref': ['aff1']},
                   {'affiliation': ['School of Engineering and Applied Sciences, Harvard University, Cambridge, MA 02138, USA',
                                    'Department of Organismic and Evolutionary Biology, Harvard University, Cambridge, MA 02138, USA',
                                    'Department of Physics, Harvard University, Cambridge, MA 02138, USA',
                                    'Wyss Institute for Biologically Inspired Engineering, Harvard University, Cambridge, MA 02138, USA',
                                    'Kavli Institute for Nanobio Science and Technology, Harvard University, Cambridge, MA 02138, USA',
                                    'Department of Systems Biology, Harvard Medical School, Boston, MA 02115, USA'],
                    'surname': 'Mahadevan',
                    'given_name': 'L.',
                    'cross_ref': ['aff2', 'aff3', 'aff4', 'aff5', 'aff6', 'aff7']},
                   {'affiliation': ['Department of Genetics, Harvard Medical School, Boston, MA 02115, USA'],
                    'cross_ref': ['aff1', 'cor1'],
                    'surname': 'Tabin',
                    'given_name': 'Clifford\xc2\xa0J.',
                    'email': 'tabin@genetics.med.harvard.edu'}]
        self.assertEqual(self.els.get_authors(self.document540), authors)

    def test_copyright(self):
        """Test that copyright is good."""
        self.assertEqual(self.els.get_copyright(self.document), '')

    def test_540_copyright(self):
        """Test that copyright is good."""
        self.assertEqual(self.els.get_copyright(self.document540), 'Elsevier Inc.')

    #Need to find a better example package for DTD5.2 version - this on doesnt have issue.xml and we have unmatching issue and main files
    @unittest.skip("Issue and main xml are not matching")
    def test_publication_information(self):
        """Test that pubinfo is good."""
        self.els._found_issues = [pkg_resources.resource_filename('harvestingkit.tests', os.path.join('data', 'sample_elsevier_issue'))]
        self.els._build_doi_mapping()
        publication_information = ('Phys.Lett.',
                                   '0370-2693',
                                   'B206',
                                   '3',
                                   '421',
                                   '426',
                                   '1988',
                                   '1988-05-26',
                                   '10.1016/j.nuclphysb.2015.07.011')
        self.assertEqual(self.els.get_publication_information(self.document), publication_information)

    def test_540_publication_information(self):
        """Test that pubinfo is good."""
        self.els._found_issues = [pkg_resources.resource_filename('harvestingkit.tests', os.path.join('data', 'sample_elsevier_540_issue'))]
        self.els._build_doi_mapping()
        publication_information = ('CELL',
                                   '0092-8674',
                                   '161',
                                   '3',
                                   '569',
                                   '580',
                                   '2015',
                                   '2015-04-23',
                                   '10.1016/j.cell.2015.03.041')
        self.assertEqual(self.els.get_publication_information(self.document540), publication_information)

    @unittest.skip("Not done yet")
    def test_references(self):
        """Test that references is good."""
        references = [('[1]', ['Belavin, A.A.', 'Polyakov, A.M.', 'Zamolodchikov, A.B.'], '', 'Nucl. Phys. B 241 1984', '333', '', '241', '1984', [], None, True, '', 'Nucl. Phys. B', '', [], ''),
                      ('[2]', ['Friedan, D.', 'Qiu, Z.', 'Shenker, S.H.'], '', 'Phys. Rev. Lett. 52 1984', '1575', '', '52', '1984', [], None, True, '', 'Phys. Rev. Lett.', '', [], ''),
                      ('[3]', ['Cardy, J.L.'], '', 'Nucl. Phys. B 270 1986', '186', '', '270', '1986', [], None, True, '[FS16]', 'Nucl. Phys. B', '', [], ''),
                      ('[3]', ['Capelli, A.', 'Itzykson, C.', 'Zuber, J.-B.'], '', 'Nucl. Phys. B 280 1987', '445', '', '280', '1987', [], None, True, '[FS 18]', 'Nucl. Phys. B', '', [], ''),
                      ('[3]', ['Capelli, A.', 'Itzykson, C.', 'Zuber, J.-B.'], '', 'Commun. Math. Phys. 113 1987', '1', '', '113', '1987', [], None, True, '', 'Commun. Math. Phys.', '', [], ''),
                      ('[3]', ['Gepner, D.'], '', 'Nucl. Phys. B 287 1987', '111', '', '287', '1987', [], None, True, '', 'Nucl. Phys. B', '', [], ''),
                      ('[4]', [], '', '', '', '', '', '', 'G. Anderson and G. Moore, IAS preprint IASSNS-HEP-87/69.', None, [], '', '', '', [], ''),
                      ('[5]', ['Friedan, D.', 'Shenker, S.'], '', 'Phys. Lett. B 175 1986', '287', '', '175', '1986', [], None, True, '', 'Phys. Lett. B', '', [], ''),
                      ('[5]', ['Friedan, D.', 'Shenker, S.'], '', 'Nucl. Phys. B 281 1987', '509', '', '281', '1987', [], None, True, '', 'Nucl. Phys. B', '', [], ''),
                      ('[6]', [], '', '', '', '', '', '', 'E. Martinec and S. Shenker, unpublished.', None, [], '', '', '', [], ''),
                      ('[7]', ['Vafa, C.'], '', 'Phys. Lett. B 199 1987', '195', '', '199', '1987', [], None, True, '', 'Phys. Lett. B', '', [], ''),
                      ('[8]', ['Harer, J.'], '', 'Inv. Math. 72 1983', '221', '', '72', '1983', [], None, True, '', 'Inv. Math.', '', [], ''),
                      ('[9]', ['Tsuchiya, A.', 'Kanie, Y.'], '', 'Lett. Math. Phys. 13 1987', '303', '', '13', '1987', [], None, True, '', 'Lett. Math. Phys.', '', [], ''),
                      ('[10]', [], '', '', '', '', '', '', 'E. Verlinde, to be published.', None, [], '', '', '', [], ''),
                      ('[11]', ['Dehn, M.'], '', 'Acta Math. 69 1938', '135', '', '69', '1938', [], None, True, '', 'Acta Math.', '', [], ''),
                      ('[12]', [], '', '', '', '', '', '', 'D. Friedan and S. Shenker, unpublished.', None, [], '', '', '', [], ''),
                      ('[13]', [], '', '', '', '', '', '', 'J. Harvey, G. Moore, and C. Vafa, Nucl. Phys. B, to be published', None, [], '', '', '', [], ''),
                      ('[14]', [], '', '', '', '', '', '', 'D. Kastor, E. Martinec and Z. Qiu, E. Fermi Institute preprint EFI-87-58.', None, [], '', '', '', [], '')]
        for ref in self.els.get_references(self.document):
            self.assertTrue(ref in references)

    @unittest.skip("Not done yet")
    def test_get_record(self):
        """Test that the whole record is correct."""
        source_file = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_document_output.xml'))
        marc_file = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_elsevier_record.xml')
        )
        self.els._found_issues = [pkg_resources.resource_filename('harvestingkit.tests', os.path.join('data', 'sample_elsevier_issue'))]
        self.els._build_doi_mapping()
        xml = self.els.get_record(source_file, test=True, no_pdf=True)
        with open(marc_file) as marc:
            result = marc.read()
        self.assertEqual(xml.strip(), result.strip())


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ElsevierPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
