# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2014, 2015 CERN.
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

from os.path import (join,
                     dirname)
from xml.dom.minidom import parse

from harvestingkit.world_scientific_package import WorldScientific
from harvestingkit.tests import (__file__ as folder,
                                 ws_test_record,
                                 ws_erratum_test_record,
                                 ws_output,
                                 ws_erratum_output,
                                 journal_mappings)


class WorldScientificTests(unittest.TestCase):

    """Test WorldScientific package."""

    def setUp(self):
        self.ws = WorldScientific(journal_mappings)
        self.ws.document = parse(join(dirname(folder), ws_test_record))

    def test_abstract(self):
        abstract = (
            u"<p><roman>CH</roman><sub>3</sub><roman>NH</roman><sub>3</sub><roman>PbX</roman>(<roman>X</roman> = <roman>Br</roman>,"
            u" <roman>I</roman>, <roman>Cl</roman>) perovskites have recently been used as light absorbers in hybrid organic-inorganic"
            u" solid-state solar cells, with efficiencies above 15%. To date, it is essential to add Lithium bis(Trifluoromethanesulfonyl)Imide"
            u" (<roman>LiTFSI</roman>) to the hole transport materials (HTM) to get a higher conductivity. However, the detrimental effect of high"
            u" <roman>LiTFSI</roman> concentration on the charge transport, DOS in the conduction band of the <roman>TiO</roman><sub>2</sub> substrate"
            u" and device stability results in an overall compromise for a satisfactory device. Using a higher mobility hole conductor to avoid lithium"
            u" salt is an interesting alternative. Herein, we successfully made an efficient perovskite solar cell by applying a hole conductor PTAA"
            u" (Poly[bis(4-phenyl) (2,4,6-trimethylphenyl)-amine]) in the absence of <roman>LiTFSI</roman>. Under AM 1.5 illumination of 100 mW/cm<sup>2</sup>,"
            u" an efficiency of 10.9% was achieved, which is comparable to the efficiency of 12.3% with the addition of 1.3 mM <roman>LiTFSI</roman>."
            u" An unsealed device without <roman>Li</roman><sup>+</sup> shows interestingly a promising stability.</p>")
        self.assertEqual(self.ws._get_abstract(), abstract)

    def test_journal(self):
        self.assertEqual(self.ws._get_journal(), 'NANO')

    def test_publisher(self):
        self.assertEqual(self.ws._get_publisher(), 'World Scientific Publishing Company')

    def test_date(self):
        self.assertEqual(self.ws._get_date(), '2014-06-05')

    def test_title(self):
        title = (u'HIGH-EFFICIENT SOLID-STATE PEROVSKITE SOLAR CELL WITHOUT LITHIUM SALT IN THE HOLE TRANSPORT MATERIAL',
                 '', [])
        self.assertEqual(self.ws._get_title(), title)

    def test_doi(self):
        self.assertEqual(self.ws._get_doi(), u'10.1142/S1793292014400013')

    def test_page_count(self):
        self.assertEqual(self.ws._get_page_count(), u'7')

    def test_authors(self):
        authors = [('Bi, Dongqin',
                    ['Department of Chemistry-Angstrom Laboratory, Uppsala University, Box 532, SE 751 20 Uppsala, Sweden'],
                    [],
                    []),
                   ('Boschloo, Gerrit',
                    ['Department of Chemistry-Angstrom Laboratory, Uppsala University, Box 532, SE 751 20 Uppsala, Sweden'],
                    [],
                    []),
                   ('Hagfeldt, Anders',
                    ['Department of Chemistry-Angstrom Laboratory, Uppsala University, Box 532, SE 751 20 Uppsala, Sweden',
                     'School of Chemical Engineering, Sungkyunkwan University, Suwon 440-746, Korea'],
                    ['anders.hagfeldt@kemi.uu.se'],
                    ['for the Belle Collaboration'])
                   ]
        self.assertEqual(self.ws._get_authors(), authors)

    def test_pacscodes(self):
        self.assertEqual(self.ws._get_pacscodes(), [])

    def test_subject(self):
        self.assertEqual(self.ws._get_subject(), '')

    def test_copyright(self):
        self.assertEqual(self.ws._get_copyright(), ('World Scientific Publishing Company', '2014', ''))

    def test_publication_information(self):
        publication_information = ('NANO',
                                   '9',
                                   '05',
                                   '2014',
                                   '2014-06-05',
                                   u'10.1142/S1793292014400013',
                                   '1440001',
                                   '',
                                   '')
        self.assertEqual(self.ws._get_publication_information(),
                         publication_information)

    def test_keywords(self):
        self.assertEqual(self.ws._get_keywords(), ['Perovskite CH 3 NH 3 PbI 3', 'solar cell', 'lithium'])

    def test_article_type(self):
        self.assertEqual(self.ws._get_article_type(), 'research-article')

    def test_related_article(self):
        self.ws.document = parse(join(dirname(folder), ws_erratum_test_record))
        related_article = '10.1142/S0129183108012303'
        self.assertEqual(self.ws._get_related_article(), related_article)

    def test_get_record(self):
        source_file = join(dirname(folder), ws_test_record)
        marc_file = join(dirname(folder), ws_output)
        xml = self.ws.get_record(source_file)
        with open(marc_file) as marc:
            result = marc.read()
        self.assertEqual(xml.strip(), result.strip())

        source_file_erratum = join(dirname(folder), ws_erratum_test_record)
        marc_file_erratum = join(dirname(folder), ws_erratum_output)
        erratum_xml = self.ws.get_record(source_file_erratum)
        with open(marc_file_erratum) as marc:
            result = marc.read()
        self.assertEqual(erratum_xml.strip(), result.strip())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        WorldScientificTests
    )
    unittest.TextTestRunner(verbosity=2).run(suite)
