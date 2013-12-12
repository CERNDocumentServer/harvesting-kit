from jats_utils import JATSParser
from invenio.minidom_utils import (get_value_in_tag,
                                   xml_to_text,
                                   NoDOIError,
                                   format_arxiv_id)


class NLMParser(JATSParser):
    def __init__(self):
        super(NLMParser, self).__init__()

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ref"):
            plain_text = None
            ref_type = reference.getElementsByTagName('mixed-citation')[0].getAttribute('publication-type').encode('utf-8')
            label = get_value_in_tag(reference, "label").strip('.')
            authors = []
            for author in reference.getElementsByTagName("name"):
                given_name = get_value_in_tag(author, "given-names")
                surname = get_value_in_tag(author, "surname")
                if given_name:
                    name = "%s, %s" % (surname, given_name)
                else:
                    name = surname
                if name.strip().split() == []:
                    name = get_value_in_tag(author, "string-name")
                authors.append(name)
            doi_tag = reference.getElementsByTagName("pub-id")
            doi = ""
            for tag in doi_tag:
                if tag.getAttribute("pub-id-type") == "doi":
                    doi = xml_to_text(tag)
            issue = get_value_in_tag(reference, "issue")
            page = get_value_in_tag(reference, "fpage")
            page_last = get_value_in_tag(reference, "lpage")
            title = get_value_in_tag(reference, "source")
            volume = get_value_in_tag(reference, "volume")
            year = get_value_in_tag(reference, "year")
            ext_link = format_arxiv_id(self.get_ref_link(reference, "arxiv"))
            if ref_type != 'journal':
                plain_text = get_value_in_tag(reference, "mixed-citation")
            references.append((label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text))
        self.references = references
