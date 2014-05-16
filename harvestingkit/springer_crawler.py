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
import getopt
import sys
import urllib2
import urlparse
import re
from os import close, remove
from bs4 import BeautifulSoup
from invenio.bibrecord import record_add_field, record_xml_output
from harvestingkit.minidom_utils import xml_to_text
from harvestingkit.utils import collapse_initials
from xml.dom.minidom import parseString
from xml.dom import getDOMImplementation
from invenio.refextract_api import extract_references_from_string_xml
from tempfile import mkstemp


class SpringerCrawler(object):
    """
    This class is specialized in crawling from Springer web pages
    for Journals, Books, Protocols and Reference works and creating
    a marc xml file containing the records of the collection
    with the link to the fulltext pdf and every posible metadata.
    """
    def __init__(self):
        self.base_url = 'http://link.springer.com/'

    def _find(self, tag, attrs):
        try:
            return self.content.find(tag, attrs=attrs).text
        except AttributeError:
            return ''

    def get_records(self, url):
        """
        Returns the records listed in the webpage given as
        parameter as a xml String.

        @param url: the url of the Journal, Book, Protocol or Reference work
        """
        page = urllib2.urlopen(url)
        page = BeautifulSoup(page)
        links = page.body.findAll('p', attrs={'class': 'title'})
        links += page.body.findAll('h3', attrs={'class': 'title'})
        impl = getDOMImplementation()
        doc = impl.createDocument(None, "collection", None)
        for link in links:
            record = self._get_record(link)
            doc.firstChild.appendChild(record)
        return doc.toprettyxml()

    def _get_record(self, link):
        link = link.find('a')['href']
        url = urlparse.urljoin(self.base_url, link)
        page = urllib2.urlopen(url)
        page = BeautifulSoup(page)
        self.content = page.body.find('div', attrs={'id': 'content'})

        publication_title = self.content.find('div', {'id': 'publication-title'})
        if publication_title:
            publication_title = publication_title.find('a').text
        else:
            publication_title = ''
        series_title = self._find('a', {'id': 'series-title'})
        if series_title == 'NATO Science Series':
            series_title = 'NATO Sci.Ser.'
        title = self._find('h1', {'id': 'title'})
        volume = self._find('span', {'id': 'book-volume'})
        if volume:
            volume = re.sub(r'\D', '', volume)
        else:
            volume = self._find('span', {'id': 'volume-range'})
            volume = re.sub(r'\D', '', volume)
        issue = self._find('a', {'id': 'issue-range'})
        if issue:
            issue = issue.split()[1]
        year = self._find('span', {'id': 'copyright-year'})
        year = re.sub(r'\D', '', year)
        if not year:
            year = self._find('dd', {'id': 'abstract-about-cover-date'})
            year = re.sub(r'\D', '', year)[:4]
        abstract = self._find('div', {'class': 'abstract-content formatted'})
        page_range = self._find('span', {'id': 'page-range'})
        if page_range:
            page_range = page_range.replace('pp', '').strip()
        publisher = self._find('dd', {'id': 'abstract-about-publisher'})
        copyright_holder = self._find('dd', {'id': 'abstract-about-book-copyright-holder'})
        issn = self._find('dd', {'id': 'abstract-about-book-series-print-issn'})
        doi = self._find('dd', {'class': 'doi'})
        subtitle = self._find('dd', {'id': 'abstract-about-book-series-subtitle'})
        online_isbn = self._find('dd', {'id': 'abstract-about-book-online-isbn'})
        print_isbn = self._find('dd', {'id': 'abstract-about-book-print-isbn'})
        editors = []
        editors_affiliations = []
        for editor in self.content.findAll('li', attrs={'itemprop': 'editor'}):
            editors.append(editor.find('a').text)
            try:
                editors_affiliations.append(editor.find('sup')['title'])
            except KeyError:
                editors_affiliations.append('')
            except TypeError:
                editors_affiliations.append('')
        authors = []
        authors_affiliations = []
        summary = self.content.find('div', attrs={'class': 'summary'})
        for author in summary.findAll('li', attrs={'itemprop': 'author'}):
            author_name = author.find('a').text
            author_names = []
            author_names.append(author_name.split()[-1] + ",")
            author_names += author_name.split()[:-1]
            author_name = " ".join(author_names)
            author_name = collapse_initials(author_name)
            authors.append(author_name)
            try:
                authors_affiliations.append(author.find('sup')['title'])
            except KeyError:
                authors_affiliations.append('')
            except TypeError:
                authors_affiliations.append('')
        try:
            attrs = {'id': 'abstract-actions-download-chapter-pdf-link'}
            fulltext = self.content.find('a', attrs=attrs)
            fulltext = urlparse.urljoin(self.base_url, fulltext['href'])
        except TypeError:
            fulltext = ''

        #create marc record
        rec = {}
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        first_author = True
        for i in range(len(authors)):
            subfields = [('a', '%s' % (authors[i]))]
            if authors_affiliations[i]:
                subfields.append(('v', authors_affiliations[i]))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract), ('9', 'Springer')])
        if copyright_holder:
            record_add_field(rec, '542', subfields=[('f', copyright_holder), ('g', year)])
        if not series_title:
            series_title = publication_title

        subfields = []
        if series_title:
            subfields.append(('p', series_title))
        if volume:
            subfields.append(('v', volume))
        if issue:
            subfields.append(('n', issue))
        if page_range:
            subfields.append(('c', page_range))
        if year:
            subfields.append(('y', year))

        record_add_field(rec, '773', subfields=subfields)
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        record_add_field(rec, '980', subfields=[('a', 'BookChapter')])

        if fulltext:
            record_add_field(rec, 'FFT', subfields=[('a', fulltext),
                                                    ('t', 'Springer'),
                                                    ('d', 'Fulltext')])

        recordString = record_xml_output(rec)
        #removes whitespaces except spaces
        recordString = re.sub(r'[\n\t\r\f\v]', '', recordString)
        #removes two or more consecutive spaces
        recordString = re.sub(r' {2,}', '', recordString)
        record = parseString(recordString)

        references = []
        ref_fields = []
        references_container = self.content.find('div', attrs={'id': 'abstract-references'})
        if references_container:
            references = references_container.findAll('li')
            for reference in references:
                ref = xml_to_text(parseString(reference.decode()))
                #removes the space between hep-th/ and the identifier
                ref = re.sub(r'hep-th/\s(\d*)', r'hep-th/\1', ref)
                ref = extract_references_from_string_xml(ref)
                ref = parseString(ref)
                for field in ref.childNodes:
                    for subfield in field.getElementsByTagName('subfield'):
                        if subfield.getAttribute('code') == 'm':
                            text = subfield.firstChild.data
                            text = re.sub(r'\[?arXiv:', '', text)
                            text = text.replace('CrossRef', '')
                            if text.startswith(': '):
                                text = text[2:]
                            if text:
                                subfield.firstChild.data = text
                            else:
                                parentNode = subfield.parentNode
                                parentNode.removeChild(subfield)
                    ref_fields.append(field.firstChild)
            for field in ref_fields:
                record.firstChild.appendChild(field)
        return record.firstChild


if __name__ == '__main__':
    usage = """
        python springer_crawler.py url_to_crawl [outputfile]
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 2:
            raise getopt.GetoptError("Too many arguments given!!!")
        elif not args:
            raise getopt.GetoptError("Missing mandatory argument url_to_crawl")
    except getopt.GetoptError as err:
        print str(err)  # will print something like "option -a not recognized"
        print usage
        sys.exit(2)
    sc = SpringerCrawler()
    url = args[0]
    if len(args) > 1:
        outfile = args[1]
    else:
        try:
            file_fd, outfile = mkstemp('.xml', 'springer_crawler', '.')
            close(file_fd)
        except IOError, e:
            try:
                remove(filepath)
            except Exception:
                pass
            raise e
    with open(outfile, 'w') as f:
        print >> f, sc.get_records(url)
