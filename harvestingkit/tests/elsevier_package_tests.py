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


class ElsevierPackageTests(unittest.TestCase):

    """Test extraction of Elsevier records."""

    def setUp(self):
        """Setup initial document."""
        self.els = ElsevierPackage(CONSYN=True,
                                   journal_mappings=journal_mappings)
        self.document = parse(pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_consyn_record.xml')
        ))

    def test_doi(self):
        """Test that doi is good."""
        self.assertEqual(self.els._get_doi(self.document), '10.1016/0370-2693(88)91603-6')

    def test_title(self):
        """Test that title is good."""
        self.assertEqual(self.els.get_title(self.document), 'Toward classification of conformal theories')

    def test_doctype(self):
        """Test that doctype is good."""
        self.assertEqual(self.els.get_doctype(self.document), 'fla')

    def test_abstract(self):
        """Test that abstract is good."""
        abstract = 'By studying the representations of the mapping class groups '\
                   'which arise in 2D conformal theories we derive some restrictions '\
                   'on the value of the conformal dimension h i of operators and the '\
                   'central charge c of the Virasoro algebra. As a simple application '\
                   'we show that when there are a finite number of operators in the '\
                   'conformal algebra, the h i and c are all rational.'
        self.assertEqual(self.els.get_abstract(self.document), abstract)

    def test_keywords(self):
        """Test that keywords are good."""
        keywords = ['Heavy quarkonia', 'Quark gluon plasma', 'Mott effect', 'X(3872)']
        self.assertEqual(self.els.get_keywords(self.document), keywords)

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
        authors = [{'affiliation': ['Lyman Laboratory of Physics, Harvard University, Cambridge, MA 02138, USA'], 'surname': 'Vafa', 'given_name': 'Cumrun', 'orcid': 'ORCID:1234-5678-4321-8765'}]
        self.assertEqual(self.els.get_authors(self.document), authors)

    def test_copyright(self):
        """Test that copyright is good."""
        self.assertEqual(self.els.get_copyright(self.document), 'Copyright unknown. Published by Elsevier B.V.')

    def test_publication_information(self):
        """Test that pubinfo is good."""
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

    def test_publication_date_oa(self):
        """Test that date is good from openAccessEffective."""
        data = """
        <doc xmlns:oa="http://vtw.elsevier.com/data/ns/properties/OpenAccess-1/">
        <oa:openAccessInformation>
          <oa:openAccessStatus xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            http://vtw.elsevier.com/data/voc/oa/OpenAccessStatus#Full
          </oa:openAccessStatus>
          <oa:openAccessEffective xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">2014-11-11T08:38:44Z</oa:openAccessEffective>
          <oa:sponsor xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <oa:sponsorName>SCOAP&#xB3; - Sponsoring Consortium for Open Access Publishing in Particle Physics</oa:sponsorName>
            <oa:sponsorType>http://vtw.elsevier.com/data/voc/oa/SponsorType#FundingBody</oa:sponsorType>
          </oa:sponsor>
          <oa:userLicense xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">http://creativecommons.org/licenses/by/3.0/</oa:userLicense>
        </oa:openAccessInformation>
        </doc>"""
        doc = parseString(data)
        self.assertEqual(
            self.els.get_publication_date(doc),
            "2014-11-11"
        )

    def test_publication_date_cover_display(self):
        """Test that date is good from coverDisplayDate."""
        data = """
        <doc xmlns:prism="http://vtw.elsevier.com/data/ns/properties/OpenAccess-1/">
          <prism:coverDisplayDate>December 2014</prism:coverDisplayDate>
        </doc>"""
        doc = parseString(data)
        self.assertEqual(
            self.els.get_publication_date(doc),
            "2014-12"
        )

    def test_publication_date_cover_display_full(self):
        """Test that date is good from coverDisplayDate."""
        data = """
        <doc xmlns:prism="http://vtw.elsevier.com/data/ns/properties/OpenAccess-1/">
          <prism:coverDisplayDate>1 December 2014</prism:coverDisplayDate>
        </doc>"""
        doc = parseString(data)
        self.assertEqual(
            self.els.get_publication_date(doc),
            "2014-12-01"
        )

    def test_publication_date_cover(self):
        """Test that date is good."""
        data = """
        <doc xmlns:prism="http://vtw.elsevier.com/data/ns/properties/OpenAccess-1/">
          <prism:coverDisplayDate>April 2011</prism:coverDisplayDate>
          <prism:coverDate>2011-04-01</prism:coverDate>
        </doc>"""
        doc = parseString(data)
        self.assertEqual(
            self.els.get_publication_date(doc),
            "2011-04-01"
        )

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
                      ('[14]', [], '', '', '', '', '', '', 'D. Kastor, E. Martinec and Z. Qiu, E. Fermi Institute preprint EFI-87-58.', None, [], '', '', '', [], ''),
                      ('[15]', ['Adeva, B.'], '', 'Phys. Rev. D 58 1998', '112001', '', '58', '1998', [], None, True, '', 'Phys. Rev. D', '', [], '')]
        for ref in self.els.get_references(self.document):
            self.assertTrue(ref in references)

    def test_get_record(self):
        """Test that the whole record is correct."""
        source_file = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_consyn_record.xml')
        )
        marc_file = pkg_resources.resource_filename(
            'harvestingkit.tests',
            os.path.join('data', 'sample_consyn_output.xml')
        )
        xml = self.els.get_record(source_file, test=True)
        with open(marc_file) as marc:
            result = marc.read()
        self.assertEqual(xml.strip(), result.strip())

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ElsevierPackageTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
