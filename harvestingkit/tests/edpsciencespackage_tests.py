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
from harvestingkit.edpsciences_package import EDPSciencesPackage
from xml.dom.minidom import parse
from os.path import (join,
                     dirname)
from harvestingkit.tests import (__file__ as folder,
                                 edp_test_record,
                                 edp_output,
                                 journal_mappings)


class EDPSciencesPackageTests(unittest.TestCase):
    def setUp(self):
        self.edp = EDPSciencesPackage(journal_mappings)
        self.edp.document = parse(join(dirname(folder), edp_test_record))

    def test_abstract(self):
        abstract = (
            u'<p><italic>Context. </italic>The depletion of iron and sulphur into dust in the interstellar'
            u' medium and the exact nature of interstellar amorphous silicate grains is still an open question.'
            u'</p> <p><italic>Aims. </italic>We study the incorporation of iron and sulphur into amorphous '
            u'silicates of olivine- and pyroxene-types and their effects on the dust spectroscopy and thermal'
            u' emission.</p> <p><italic>Methods. </italic>We used the Maxwell-Garnett effective-medium theory to'
            u' construct the optical constants for a mixture of silicates, metallic iron, and iron sulphide. '
            u'We also studied the effects of iron and iron sulphide in aggregate grains.</p> <p><italic>Results.'
            u' </italic>Iron sulphide inclusions within amorphous silicates that contain iron metal inclusions'
            u' show no strong differences in the optical properties of the grains. A mix of amorphous olivine-'
            u' and pyroxene-type silicate broadens the silicate features. An amorphous carbon mantle with a'
            u' thickness of 10 nm on the silicate grains leads to an increase in absorption on the short-wavelength '
            u'side of the 10 <inline-formula specific-use="simple-math"><italic>μ</italic></inline-formula>'
            u'm silicate band.</p> <p><italic>Conclusions. </italic>The assumption of amorphous olivine-type and'
            u' pyroxene-type silicates and a 10 nm thick amorphous carbon mantle better matches the interstellar'
            u' silicate band profiles. Including iron nano-particles leads to an increase in the mid-IR extinction,'
            u' while up to 5 ppm of sulphur can be incorporated as Fe/FeS nano inclusions into silicate grains '
            u'without leaving a significant trace of its presence.</p>')
        self.assertEqual(self.edp._get_abstract(), abstract)

    def test_journal(self):
        self.assertEqual(self.edp._get_journal(), 'A&A')

    def test_publisher(self):
        self.assertEqual(self.edp._get_publisher(), 'EDP Sciences')

    def test_date(self):
        self.assertEqual(self.edp._get_date(), '2014-05-23')

    def test_title(self):
        title = u'A dearth of small particles in debris disks', 'An energy-constrained smallest fragment size', [u'FN1']
        self.assertEqual(self.edp._get_title(), title)

    def test_doi(self):
        self.assertEqual(self.edp._get_doi(), u'10.1051/0004-6361/201423985')

    def test_page_count(self):
        self.assertEqual(self.edp._get_page_count(), u'4')

    def test_authors(self):
        authors = [('Krause, Martin', [u'AFF1', u'AFF2'], []),
                   ('K\xc3\xb6hler, M.', [], []),
                   ('Jones, A.', [], []),
                   ('Ysard, N.', [], [])]
        self.assertEqual(self.edp._get_authors(), authors)

    def test_pacscodes(self):
        self.assertEqual(self.edp._get_pacscodes(), [])

    def test_copyright(self):
        self.assertEqual(self.edp._get_copyright(), ('ESO', '2014', '\xc2\xa9 ESO, 2014'))

    def test_publication_information(self):
        publication_information = ('Astron.Astrophys.',
                                   '565',
                                   '',
                                   u'2014',
                                   '2014-05-23',
                                   u'10.1051/0004-6361/201423985',
                                   'L9',
                                   '925',
                                   '')
        self.assertEqual(self.edp._get_publication_information(), publication_information)

    def test_affiliations(self):
        affiliations = {u'AFF1': 'Institut d\xe2\x80\x99Astrophysique Spatiale (IAS), Universit\xc3\xa9 Paris-Sud & CNRS , B\xc3\xa2t. 121 , 91405 Orsay , France',
                        u'AFF2': 'Excellence Cluster Universe, Technische Universit\xc3\xa4t M\xc3\xbcnchen , Boltzmannstrasse 2 , 85748 Garching , Germany'}
        self.assertEqual(self.edp._get_affiliations(), affiliations)

    def test_author_emails(self):
        author_emails = {u'FN1': ['mkoehler@ias.u-psud.fr']}
        self.assertEqual(self.edp._get_author_emails(), author_emails)

    def test_subject(self):
        self.assertEqual(self.edp._get_subject(), 'Letters')

    def test_license(self):
        self.assertEqual(self.edp._get_license(), ('Creative Commons Attribution License 2.0',
                                                   u'open-access-test',
                                                   u'http://creativecommons.org/licenses/by/2.0/'))

    def test_keywords(self):
        self.assertEqual(self.edp._get_keywords(), [u'dust, extinction', u'ISM: abundances'])

    def test_references(self):
        references = [(u'2', u'journal', '', '', ['Bradley, J.P.'], '1994', 'Science', '265', '925'),
                      (u'3', u'journal', '', '', ['Caselli, P.', 'Hasegawa, T.I.', 'Herbst, E.'], '1994', 'Astrophys.J.', '421', '206'),
                      (u'4', u'journal', '', '', ['Chiar, J.E.', 'Tielens, A.G.G.M.'], '2006', 'Astrophys.J.', '637', '774'),
                      (u'5', u'journal', '', '', ['Compi\xc3\xa8gne, M.', 'Verstraete, L.', 'Jones, A.'], '2011', 'Astron.Astrophys.', '525', 'A103'),
                      (u'6', u'journal', '', '', ['Costantini, E.', 'Freyberg, M.J.', 'Predehl, P.'], '2005', 'Astron.Astrophys.', '444', '187'),
                      (u'7', u'journal', '', '', ['Davoisne, C.', 'Djouadi, Z.', 'Leroux, H.'], '2006', 'Astron.Astrophys.', '448', 'L1'),
                      (u'8', u'journal', '', '', ['Demyk, K.', 'Carrez, P.', 'Leroux, H.'], '2001', 'Astron.Astrophys.', '368', 'L38'),
                      (u'9', u'journal', '', '', ['Djouadi, Z.', 'Gattacceca, J.', 'D\xe2\x80\x99Hendecourt, L.'], '2007', 'Astron.Astrophys.', '468', 'L9'),
                      (u'10', u'journal', '', '', ['Draine, B.'], '1988', 'Astrophys.J.', '333', '848'),
                      (u'12', u'journal', '', '', ['Jenkins, E.B.'], '2009', 'Astrophys.J.', '700', '1299'),
                      (u'13', u'journal', '', '', ['Jones, A.P.'], '2000', 'J.Geophys.Res.', '105', '10257'),
                      (u'14', u'journal', '', '', ['Jones, A.P.'], '2011', 'Astron.Astrophys.', '528', 'A98'),
                      (u'15', u'journal', '', '', ['Jones, R.V.', 'Spitzer, L.'], '1967', 'Astrophys.J.', '147', '943'),
                      (u'16', u'journal', '', '', ['Jones, A.P.', 'Fanciullo, L.', 'K\xc3\xb6hler, M.'], '2013', 'Astron.Astrophys.', '558', 'A62'),
                      (u'17', u'journal', '', '', ['Joseph, C.L.', 'Snow, T.P.', 'Seab, C.G.', 'Crutcher, R.M.'], '1986', 'Astrophys.J.', '309', '771'),
                      (u'18', u'journal', '', '', ['Keller, L.P.', 'Hony, S.', 'Bradley, J.P.'], '2002', 'Nature', '417', '148'),
                      (u'19', u'journal', '', '', ['Leroux, H.', 'Roskosz, M.', 'Jacob, D.'], '2009', 'Geochim.Cosmochim.Acta', '73', '767'),
                      (u'20', u'journal', '', '', ['Mathis, J.S.'], '1990', 'Ann.Rev.Astron.Astrophys.', '28', '37'),
                      (u'21', u'journal', '', '', ['McClure, M.'], '2009', 'Astrophys.J.', '693', 'L81'),
                      (u'22', u'journal', '', '', ['Millar, T.J.', 'Herbst, E.'], '1990', 'Astron.Astrophys.', '231', '466'),
                      (u'23', u'journal', '', '', ['Min, M.', 'Waters, L.B.F.M.', 'de Koter, A.'], '2007', 'Astron.Astrophys.', '462', '667'),
                      (u'24', u'journal', '', '', ['Nguyen, A.N.', 'Stadermann, F.J.', 'Zinner, E.'], '2007', 'Astrophys.J.', '656', '1223'),
                      (u'25', u'journal', '', '', ['Ordal, M.A.', 'Bell, R.J.', 'Alexander, R.W.', 'Long, L.L.', 'Querry, M.R.'], '1985', 'Appl.Opt.', '24', '4493'),
                      (u'26', u'journal', '', '', ['Ordal, M.A.', 'Bell, R.J.', 'Alexander, R.W.', 'Newquist, L.A.', 'Querry, M.R.'], '1988', 'Appl.Opt.', '27', '1203'),
                      (u'28', u'journal', '', '', ['Pollack, J.B.', 'Hollenbach, D.', 'Beckwith, S.'], '1994', 'Astrophys.J.', '421', '615'),
                      (u'29', u'journal', '', '', ['Purcell, E.M.', 'Pennypacker, C.R.'], '1973', 'Astrophys.J.', '186', '705'),
                      (u'30', u'journal', '', '', ['Rieke, G.H.', 'Lebofsky, M.J.'], '1985', 'Astrophys.J.', '288', '618'),
                      (u'31', u'journal', '', '', ['Roskosz, M.', 'Gillot, J.', 'Capet, F.', 'Roussel, P.', 'Leroux, H.'], '2011', 'Astron.Astrophys.', '529', 'A111'),
                      (u'32', u'journal', '', '', ['Savage, B.D.', 'Bohlin, R.C.'], '1979', 'Astrophys.J.', '229', '136'),
                      (u'33', u'journal', '', '', ['Savage, B.D.', 'Mathis, J.S.'], '1979', 'Ann.Rev.Astron.Astrophys.', '17', '73'),
                      (u'34', u'journal', '', '', ['Scott, A.', 'Duley, W.W.'], '1996', 'Astrophys.J.Suppl.', '105', '401'),
                      (u'35', u'journal', '', '', ['Sofia, U.J.', 'Joseph, C.L.'], '1995', 'Bull.Am.Astron.Soc.', '27', '860'),
                      (u'36', u'journal', '', '', ['Ueda, Y.', 'Mitsuda, K.', 'Murakami, H.', 'Matsushita, K.'], '2005', 'Astrophys.J.', '620', '274'),
                      (u'37', u'journal', '', '', ['Xiang, J.', 'Lee, J.C.', 'Nowak, M.A.', 'Wilms, J.'], '2011', 'Astrophys.J.', '738', '78')]
        i = 0
        for ref in self.edp._get_references():
            self.assertEqual(ref, references[i])
            i += 1

    def test_article_type(self):
        self.assertEqual(self.edp._get_article_type(), 'research-article')

    def test_get_record(self):
        source_file = join(dirname(folder), edp_test_record)
        marc_file = join(dirname(folder), edp_output)
        xml = self.edp.get_record(source_file)
        with open(marc_file) as marc:
            result = marc.read()
        with open("/tmp/test.xml", "w") as marc:
            marc.write(xml)
        self.assertEqual(xml.strip(), result.strip())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(EDPSciencesPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
