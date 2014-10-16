import unittest

from xml.dom.minidom import Element, parseString

from harvestingkit.jats_utils import JATSParser


class JATSUtilsTests(unittest.TestCase):

    def setUp(self):
        self.jats_parser = JATSParser()
    
    def test_get_orcid(self):
        """
        See http://jats.nlm.nih.gov/archiving/tag-library/1.1d1/n-dsw0.html for orcid in contrib tag 
        """

        xml = parseString(
              """<contrib>
                   <contrib-id contrib-id-type="orcid">http://orcid.org/1792-3336-9172-961X</contrib-id>
                   <name><surname>Fauller</surname>
                   <given-names>Betty Lou</given-names>
                   </name>
                   <degrees>BA, MA</degrees>
                 </contrib>""")

        self.assertEqual(self.jats_parser._get_orcid(xml), '1792-3336-9172-961X')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(JATSUtilsTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
