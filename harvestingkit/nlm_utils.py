# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2013, 2014, 2015 CERN.
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

from harvestingkit.jats_utils import JATSParser
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.utils import (format_arxiv_id,
                                 add_nations_field)

from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
    record_xml_output,
)
try:
    from invenio.errorlib import register_exception
except ImportError:
    register_exception = lambda a=1, b=2: True
from harvestingkit.scoap3utils import MissingFFTError
from os import pardir
from os.path import (join,
                     basename,
                     dirname,
                     exists)


class NLMParser(JATSParser):
    def __init__(self, extract_nations=False):
        super(NLMParser, self).__init__()
        self.extract_nations = extract_nations

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ref"):
            plain_text = None
            refs = reference.getElementsByTagName('citation')
            if refs:
                ref_type = refs[0].getAttribute('publication-type').encode('utf-8')
            else:
                ref_type = None
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
            ext_link = format_arxiv_id(super(NLMParser, self).get_ref_link(reference, "arxiv"))
            if ref_type != 'journal':
                plain_text = get_value_in_tag(reference, "mixed-citation")
            references.append((label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text))
        self.references = references

    def get_arxiv_id(self, xml):
        custom_metas = xml.getElementsByTagName("custom-meta")
        ext_link = None
        for meta in custom_metas:
            if get_value_in_tag(meta, "meta-name") == "arxiv-id":
                ext_link = format_arxiv_id(get_value_in_tag(meta, "meta-value").encode('utf-8'))
        return ext_link

    def get_record(self, f_path, publisher=None, collection=None, logger=None):
        xml = super(NLMParser, self).get_article(f_path)
        rec = create_record()
        title = super(NLMParser, self).get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        record_add_field(rec, '260', subfields=[('c', super(NLMParser, self).get_publication_date(xml, logger))])
        journal, issn, volume, issue, first_page, last_page, year, doi = super(NLMParser, self).get_publication_information(xml)
        journal = "PTEP"  # Let's override the journal information

        if logger:
            logger.info("Creating record: %s %s" % (join(f_path, pardir), doi))

        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        page_count = super(NLMParser, self).get_page_count(xml)
        if page_count:
            record_add_field(rec, '300', subfields=[('a', page_count)])
        arxiv = self.get_arxiv_id(xml)
        if arxiv:
            record_add_field(rec, '037', subfields=[('9', 'arXiv'), ('a', format_arxiv_id(arxiv))])
        authors = super(NLMParser, self).get_authors(xml)
        first_author = True
        for author in authors:
            if author.get('surname'):
                subfields = [('a', '%s, %s' % (author.get('surname'), author.get('given_name') or author.get('initials', '')))]
            else:
                subfields = [('a', '%s' % (author.get('name', '')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('v', aff))

                if self.extract_nations:
                    add_nations_field(subfields)

            if author.get('email'):
                    subfields.append(('m', author['email']))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)

        abstract = super(NLMParser, self).get_abstract(xml)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract), ('9', publisher)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'), ('u', 'http://creativecommons.org/licenses/by/3.0/')])
        copyright = super(NLMParser, self).get_copyright(xml, logger)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = super(NLMParser, self).get_keywords(xml)
        if keywords['pacs']:
            for keyword in keywords['pacs']:
                record_add_field(rec, '084', ind1='1', subfields=[('a', keyword), ('9', 'PACS')])

        ## Oxford is giving us bad keywords. Better ignore them.
        #if keywords['other']:
            #for keyword in keywords['other']:
                #record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        if first_page or last_page:
            pages = '%s-%s' % (first_page, last_page)
        else:
            article_meta = xml.getElementsByTagName('article-meta')[0]
            pages = get_value_in_tag(article_meta, "elocation-id")

        subfields = filter(lambda x: x[1] and x[1] != '-', [('p', journal),
                                                            ('v', volume),
                                                            ('n', issue),
                                                            ('c', pages),
                                                            ('y', year)])
        record_add_field(rec, '773', subfields=subfields)

        self.get_references(xml)
        for label, authors, doi, issue, page, page_last, title, volume, year, ext_link, plain_text in self.references:
            subfields = []
            if doi:
                subfields.append(('a', doi))
            for author in authors:
                subfields.append(('h', author))
            if issue:
                subfields.append(('n', issue))
            if label:
                subfields.append(('o', label))
            if year:
                subfields.append(('y', year))
            if ext_link:
                subfields.append(('r', ext_link))
            # should we be strict about it?
            if title and volume and year and page:
                subfields.append(('s', '%s %s (%s) %s' % (title, volume, year, page)))
            elif not plain_text:
                subfields.append(('m', ('%s %s %s %s' % (title, volume, year, page))))
            if plain_text:
                subfields.append(('m', plain_text))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
        f_path_pdf = f_path[:-(len('.xml'))] + '.pdf'
        f_path_pdfa = join(dirname(f_path), 'archival_pdfs', basename(f_path)[:-len('.xml')] + '-hires.pdf')
        if exists(f_path_pdf):
            record_add_field(rec, 'FFT', subfields=[('a', f_path_pdf), ('n', 'main')])
        else:
            try:
                raise MissingFFTError
            except:
                register_exception(alert_admin=True, prefix="Oxford paper: %s is missing PDF." % (doi,))
                logger.warning("Record %s doesn't contain PDF file." % (doi,))
        if exists(f_path_pdfa):
            record_add_field(rec, 'FFT', subfields=[('a', f_path_pdfa), ('n', 'main'), ('f', '.pdf;pdfa')])
        else:
            try:
                raise MissingFFTError
            except:
                register_exception(alert_admin=True, prefix="Oxford paper: %s is missing PDF/A." % (doi,))
                logger.warning("Record %s doesn't contain PDF/A file." % (doi,))
        record_add_field(rec, 'FFT', subfields=[('a', f_path), ('n', 'main')])
        extra_subfields = []
        if collection:
            extra_subfields.append(('a', collection))
        if publisher:
            extra_subfields.append(('b', publisher))
        record_add_field(rec, '980', subfields=extra_subfields)
        return record_xml_output(rec)
