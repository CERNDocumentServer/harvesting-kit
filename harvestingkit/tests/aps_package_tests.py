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
from harvestingkit.aps_package import ApsPackage
from xml.dom.minidom import parse
from os.path import (join,
                     dirname)
from harvestingkit.tests import (__file__ as folder,
                                 aps_test_record,
                                 journal_mappings)


class APSPackageTests(unittest.TestCase):
    def setUp(self):
        self.aps = ApsPackage(journal_mappings)
        self.aps.document = parse(join(dirname(folder), aps_test_record))

    def test_journal(self):
        self.assertEqual(self.aps._get_journal(), 'Phys.Rev.C')

    def test_abstract(self):
        abstract = 'We calculate the effective masses of neutrons and protons '\
                   'in dense nuclear matter within the microscopic Brueckner-Hartree-Fock '\
                   'many-body theory and study the impact on the neutrino emissivity '\
                   'processes of neutron stars. We compare results based on different '\
                   'nucleon-nucleon potentials and nuclear three-body forces. Useful '\
                   'parametrizations of the numerical results are given. We find '\
                   'substantial in-medium suppression of the emissivities, '\
                   'strongly dependent on the interactions.'
        self.assertEqual(self.aps._get_abstract(), abstract)

    def test_title(self):
        title = 'Nucleon effective masses within the Brueckner-Hartree-Fock '\
                'theory: Impact on stellar neutrino emission', '', []
        self.assertEqual(self.aps._get_title(), title)

    def test_doi(self):
        self.assertEqual(self.aps._get_doi(), '10.1103/PhysRevC.89.048801')

    def test_authors(self):
        authors = [('Baldo, M.', [], ''),
                   ('Burgio, G.F.', [], ''),
                   ('Schulze, H.-J.', [], ''),
                   ('Newman, M.E.J.', [u'a2', u'a3'], ''),
                   ('Taranto, G.', [u'a1'], u'n1')]
        self.assertEqual(self.aps._get_authors(), authors)

    def test_affiliations(self):
        affiliations = {u'a1': 'INFN Sezione di Catania and Dipartimento di Fisica e Astronomia, Universit\xc3\xa1 di Catania , Via Santa Sofia 64, 95123 Catania, Italy', u'a3': 'Center for the Study of Complex Systems, University of Michigan , Ann Arbor, Michigan 48109, USA', u'a2': 'Department of Electrical Engineering and Computer Science, University of Michigan , Ann Arbor, Michigan 48109, USA'}
        self.assertEqual(self.aps._get_affiliations(), affiliations)

    def test_author_emails(self):
        emails = {u'n1': ['tarantogabriele@gmail.com', 'gabriele.taranto@ct.infn.it']}
        self.assertEqual(self.aps._get_author_emails(), emails)

    def test_copyright(self):
        self.assertEqual(self.aps._get_copyright(), ('American Physical Society', '2014', '\xc2\xa92014 American Physical Society'))

    def test_date(self):
        self.assertEqual(self.aps._get_date(), '2014-04-28')

    def test_publisher(self):
        self.assertEqual(self.aps._get_publisher(), 'American Physical Society')

    def test_publication_information(self):
        publication_information = ('Phys.Rev.',
                                   'C89',
                                   '4',
                                   u'2014',
                                   u'2014-04-28',
                                   u'10.1103/PhysRevC.89.048801',
                                   '048801',
                                   '',
                                   '')
        self.assertEqual(self.aps._get_publication_information(), publication_information)

    def test_pagecount(self):
        self.assertEqual(self.aps._get_page_count(), '5')

    def test_pacscodes(self):
        self.assertEqual(self.aps._get_pacscodes(), ['26.60.Kp', '97.10.Cv'])

    def test_subject(self):
        self.assertEqual(self.aps._get_subject(), 'Nuclear Astrophysics')

    def test_license(self):
        self.assertEqual(self.aps._get_license(), ('', '', ''))

    def test_keywords(self):
        self.assertEqual(self.aps._get_keywords(), [])

    def test_references(self):
        references = [(u'journal', u'10.1016/S0370-1573(00)00131-9', [u'D. G. Yakovlev', u'A. D. Kaminker', u'O. Y. Gnedin', u'P. Haensel'], '', 'Phys.Rep.', '354', '1', '2001', '1', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/0370-1573(76)90017-X', [u'J. P. Jeukenne', u'A. Lejeune', u'C. Mahaux'], '', 'Phys.Rep.', 'C25', '83', '1976', '2', '', '', '', [], '', '', []),
                      (u'book', '', [u'M. Baldo'], '', 'Nuclear Methods and the Nuclear Equation of State, International Review of Nuclear Physics, Vol.8', '', '', '1999', '3', '', 'Singapore: World Scientific', '', [], '', '', []),
                      (u'journal', u'10.1088/0034-4885/75/2/026301', [u'M. Baldo', u'G. F. Burgio'], '', 'Rep.Prog.Phys.', '75', '026301', '2012', '4', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.24.1203', [u'B. D. Day'], '', 'Phys.Rev.', 'C24', '1203', '1981', '5', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevLett.81.1584', [u'H. Q. Song', u'M. Baldo', u'G. Giansiracusa', u'U. Lombardo'], '', 'Phys.Rev.Lett.', '81', '1584', '1998', '5', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/S0370-2693(99)01463-X', [u'M. Baldo', u'G. Giansiracusa', u'U. Lombardo', u'H. Q. Song'], '', 'Phys.Lett.', 'B473', '1', '2000', '5', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.65.017303', [u'M. Baldo', u'A. Fiasconaro', u'H. Q. Song', u'G. Giansiracusa', u'U. Lombardo'], '', 'Phys.Rev.', 'C65', '017303', '2001', '5', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.73.034307', [u'R. Sartor'], '', 'Phys.Rev.', 'C73', '034307', '2006', '5', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.74.047304', [u'Z. H. Li', u'U. Lombardo', u'H.-J. Schulze', u'W. Zuo', u'L. W. Chen', u'H. R. Ma'], '', 'Phys.Rev.', 'C74', '047304', '2006', '6', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.86.064001', [u'M. Baldo', u'A. Polls', u'A. Rios', u'H.-J. Schulze', u'I. Vida\xf1a'], '', 'Phys.Rev.', 'C86', '064001', '2012', '7', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.40.1040', [u'P. Grang\xe9', u'A. Lejeune', u'M. Martzolff', u'J.-F. Mathiot'], '', 'Phys.Rev.', 'C40', '1040', '1989', '8', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/S0375-9474(02)00750-9', [u'W. Zuo', u'A. Lejeune', u'U. Lombardo', u'J.-F. Mathiot'], '', 'Nucl.Phys.', 'A706', '418', '2002', '8', '', '', '', [], '', '', []),
                      (u'journal', '', [u'M. Baldo', u'I. Bombaci', u'G. F. Burgio'], '', 'Astron.Astrophys.', '328', '274', '1997', '9', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.69.018801', [u'X. R. Zhou', u'G. F. Burgio', u'U. Lombardo', u'H.-J. Schulze', u'W. Zuo'], '', 'Phys.Rev.', 'C69', '018801', '2004', '10', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.77.034316', [u'Z. H. Li', u'U. Lombardo', u'H.-J. Schulze', u'W. Zuo'], '', 'Phys.Rev.', 'C77', '034316', '2008', '11', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.85.064002', [u'Z. H. Li', u'H.-J. Schulze'], '', 'Phys.Rev.', 'C85', '064002', '2012', '11', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.88.054326', [u'A. Carbone', u'A. Cipollone', u'C. Barbieri', u'A. Rios', u'A. Polls'], '', 'Phys.Rev.', 'C88', '054326', '2013', '12', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/0375-9474(83)90336-6', [u'J. Carlson', u'V. R. Pandharipande', u'R. B. Wiringa'], '', 'Nucl.Phys.', 'A401', '59', '1983', '13', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/0375-9474(86)90003-5', [u'R. Schiavilla', u'V. R. Pandharipande', u'R. B. Wiringa'], '', 'Nucl.Phys.', 'A449', '219', '1986', '13', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.56.1720', [u'B. S. Pudliner', u'V. R. Pandharipande', u'J. Carlson', u'S. C. Pieper', u'R. B. Wiringa'], '', 'Phys.Rev.', 'C56', '1720', '1997', '13', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/j.physletb.2008.02.040', [u'M. Baldo', u'A. E. Shaban'], '', 'Phys.Lett.', 'B661', '373', '2008', '14', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.51.38', [u'R. B. Wiringa', u'V. G. J. Stoks', u'R. Schiavilla'], '', 'Phys.Rev.', 'C51', '38', '1995', '15', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.63.024001', [u'R. Machleidt'], '', 'Phys.Rev.', 'C63', '024001', '2001', '16', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.78.028801', [u'Z. H. Li', u'H.-J. Schulze'], '', 'Phys.Rev.', 'C78', '028801', '2008', '17', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.74.014317', [u'W. Zuo', u'U. Lombardo', u'H.-J. Schulze', u'Z. H. Li'], '', 'Phys.Rev.', 'C74', '014317', '2006', '18', '', '', '', [], '', '', []),
                      (u'journal', u'10.1088/0256-307X/29/4/042102', [u'S.-X. Gan', u'W. Zuo', u'U. Lombardo'], '', 'Chin.Phys.Lett.', '29', '042102', '2012', '18', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/S0370-2693(97)01600-6', [u'W. Zuo', u'G. Giansiracusa', u'U. Lombardo', u'N. Sandulescu', u'H.-J. Schulze'], '', 'Phys.Lett.', 'B421', '1', '1998', '19', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/S0370-2693(98)00656-X', [u'W. Zuo', u'U. Lombardo', u'H.-J. Schulze'], '', 'Phys.Lett.', 'B432', '241', '1998', '19', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.82.014314', [u'K. Hebeler', u'A. Schwenk'], '', 'Phys.Rev.', 'C82', '014314', '2010', '20', '', '', '', [], '', '', []),
                      (u'journal', u'10.1016/j.nuclphysa.2011.12.001', [u'J. W. Holt', u'N. Kaiser', u'W. Weise'], '', 'Nucl.Phys.', 'A876', '61', '2012', '20', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevLett.66.2701', [u'J. M. Lattimer', u'C. J. Pethick', u'M. Prakash', u'P. Haensel'], '', 'Phys.Rev.Lett.', '66', '2701', '1991', '21', '', '', '', [], '', '', []),
                      (u'journal', u'10.1086/157313', [u'B. L. Friman', u'O. V. Maxwell'], '', 'Astrophys.J.', '232', '541', '1979', '22', '', '', '', [], '', '', []),
                      (u'journal', '', [u'D. G. Yakovlev', u'K. P. Levenfish'], '', 'Astron.Astrophys.', '297', '717', '1995', '23', '', '', '', [], '', '', []),
                      (u'journal', u'10.1103/PhysRevC.88.015804', [u'Peng Yin', u'Wei Zuo'], '', 'Phys.Rev.', 'C88', '015804', '2013', '24', '', '', '', [], '', '', [])
                      ]
        for ref in self.aps.document.getElementsByTagName('ref'):
            for innerref in self.aps._get_reference(ref):
                self.assertTrue(innerref in references)

    def test_article_type(self):
        self.assertEqual(self.aps._get_article_type(), 'brief-report')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(APSPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
