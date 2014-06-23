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
from harvestingkit.elsevier_package import ElsevierPackage
from xml.dom.minidom import parse


sample_record = "sample_consyn_record.xml"


class ElsevierPackageTests(unittest.TestCase):
    def setUp(self):
        self.els = ElsevierPackage(CONSYN=True)
        self.document = parse(sample_record)

    def test_doi(self):
        self.assertEqual(self.els._get_doi(self.document), '10.1016/0370-2693(88)91603-6')

    def test_title(self):
        self.assertEqual(self.els.get_title(self.document), 'Toward classification of conformal theories')

    def test_doctype(self):
        self.assertEqual(self.els.get_doctype(self.document), 'fla')

    def test_abstract(self):
        abstract = 'By studying the representations of the mapping class groups '\
                   'which arise in 2D conformal theories we derive some restrictions '\
                   'on the value of the conformal dimension h i of operators and the '\
                   'central charge c of the Virasoro algebra. As a simple application '\
                   'we show that when there are a finite number of operators in the '\
                   'conformal algebra, the h i and c are all rational.'
        self.assertEqual(self.els.get_abstract(self.document), abstract)

    def test_keywords(self):
        keywords = ['Heavy quarkonia', 'Quark\xe2\x80\x93gluon plasma', 'Mott effect', 'X(3872)']
        self.assertEqual(self.els.get_keywords(self.document), keywords)

    def test_authors(self):
        authors = [{'affiliation': ['Lyman Laboratory of Physics, Harvard University, Cambridge, MA 02138, USA'], 'surname': 'Vafa', 'given_name': 'Cumrun'}]
        self.assertEqual(self.els.get_authors(self.document), authors)

    def test_copyritght(self):
        self.assertEqual(self.els.get_copyright(self.document), 'Copyright \xc2\xa9 unknown. Published by Elsevier B.V.')

    def test_publication_information(self):
        publication_information = ('Phys.Lett.',
                                   '0370-2693',
                                   'B206',
                                   '3',
                                   '421',
                                   '426',
                                   '1988',
                                   '1988-05-26',
                                   '10.1016/0370-2693(88)91603-6')
        self.assertEqual(self.els.get_publication_information(self.document), publication_information)

    def test_references(self):
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


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ElsevierPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
