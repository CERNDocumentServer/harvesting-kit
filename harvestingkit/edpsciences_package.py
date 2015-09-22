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

from __future__ import print_function

import sys
import requests

from bs4 import BeautifulSoup
from urlparse import urlparse
from os.path import join
from os import makedirs
from re import sub

from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.utils import (collapse_initials,
                                 fix_journal_name,
                                 download_file)
from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
    record_xml_output,
)

from xml.dom.minidom import (parse,
                             parseString)
from harvestingkit.jats_package import JatsPackage

try:
    from invenio.config import CFG_EDPSCIENCE_OUT_FOLDER
except ImportError:
    from distutils.sysconfig import get_python_lib

    CFG_EDPSCIENCE_OUT_FOLDER = join(get_python_lib(),
                                     "harvestingkit",
                                     "edpsciences")


class EDPSciencesPackage(JatsPackage):
    """
    This class is specialized in parsing files from EdpSciences FTP server
    and converting them in Marc XML.
    """
    def __init__(self, journal_mappings={}):
        super(EDPSciencesPackage, self).__init__(journal_mappings)

    def _get_references(self):
        for ref in self.document.getElementsByTagName('ref'):
            label = ref.getAttribute('id')
            label = sub(r'\D', '', label)
            text_ref = ''
            ext_link = ''
            for mixed in ref.getElementsByTagName('mixed-citation'):
                ref_type = mixed.getAttribute('publication-type')
                if ref_type == 'thesis':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                elif ref_type == 'conf-proc':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                elif ref_type == 'other' or ref_type == 'web':
                    text_ref = get_value_in_tag(ref, 'mixed-citation')
                    ext_link = get_value_in_tag(mixed, 'ext-link')
                elif ref_type == 'book':
                    text_ref = xml_to_text(mixed)
            authors = []
            for auth in ref.getElementsByTagName('string-name'):
                surname = get_value_in_tag(auth, 'surname')
                given_names = get_value_in_tag(auth, 'given-names')
                given_names = collapse_initials(given_names)
                authors.append('%s, %s' % (surname, given_names))
            year = get_value_in_tag(ref, 'year')
            source = get_value_in_tag(ref, 'source')
            volume = get_value_in_tag(ref, 'volume')
            page = get_value_in_tag(ref, 'fpage')
            if ref_type == 'journal':
                source, vol = fix_journal_name(source, self.journal_mappings)
                if vol:
                    volume = vol + volume
            yield (label, ref_type, text_ref, ext_link,
                   authors, year, source, volume, page)

    def _add_references(self, rec, ref_extract_callback=None):
        for label, ref_type, text_ref, ext_link, authors, year, \
                source, volume, page in self._get_references():
            subfields = []
            if label:
                subfields.append(('o', label))
            if text_ref:
                if ref_extract_callback:
                    ref_xml = ref_extract_callback(text_ref)
                    dom = parseString(ref_xml)
                    fields = dom.getElementsByTagName("datafield")[0]
                    fields = fields.getElementsByTagName("subfield")
                    for field in fields:
                        data = field.firstChild.data
                        code = field.getAttribute("code")
                        subfields.append((code, data))
                    if fields:
                        subfields.append(('9', 'refextract'))
                else:
                    subfields.append(('m', text_ref))
            if ref_type:
                subfields.append(('d', ref_type))
            if ext_link:
                subfields.append(('u', ext_link))
            for author in authors:
                subfields.append(('h', author))
            if year:
                subfields.append(('y', year))
            if source and volume and page:
                subfields.append(('s', source + "," + volume + "," + page))
            elif source and volume:
                subfields.append(('s', source + "," + volume))
            elif source and page:
                subfields.append(('s', source + "," + page))
            elif source:
                subfields.append(('s', source))
            record_add_field(rec, '999', ind1='C', ind2='5',
                             subfields=subfields)

    def _get_note(self, note_id):
        for tag in self.document.getElementsByTagName('fn'):
            if tag.getAttribute('id') == note_id:
                for label in tag.getElementsByTagName('label'):
                    tag.removeChild(label)
                return xml_to_text(tag)

    def get_date(self, filename):
        self.document = parse(filename)
        return self._get_date()

    def _format_abstract(self, abstract):
        abstract = abstract.replace("Context.", "Context:<br/>")
        abstract = abstract.replace("Aims.", "<br/>Aims:<br/>")
        abstract = abstract.replace("Methods.", "<br/>Methods:<br/>")
        abstract = abstract.replace("Results.", "<br/>Results:<br/>")
        abstract = abstract.replace("Conclusions..", "<br/>Conclusions:<br/>")
        return abstract

    def get_record(self, fileName, ref_extract_callback=None):
        """
        Gets the Marc xml of the files in xaml_jp directory

        :param fileName: the name of the file to parse.
        :type fileName: string
        :param refextract_callback: callback to be used to extract
                                    unstructured references. It should
                                    return a marcxml formated string
                                    of the reference.
        :type refextract_callback: callable

        :returns: a string with the marc xml version of the file.
        """
        self.document = parse(fileName)
        article_type = self._get_article_type()
        if article_type not in ['research-article',
                                'introduction',
                                'letter']:
            return ''
        rec = create_record()
        title, subtitle, notes = self._get_title()
        subfields = []
        if subtitle:
            subfields.append(('b', subtitle))
        if title:
            subfields.append(('a', title))
            record_add_field(rec, '245', subfields=subfields)
        subjects = self.document.getElementsByTagName('kwd')
        subjects = map(xml_to_text, subjects)
        for note_id in notes:
            note = self._get_note(note_id)
            if note:
                record_add_field(rec, '500', subfields=[('a', note)])
        for subject in subjects:
            record_add_field(rec, '650', ind1='1', ind2='7',
                             subfields=[('2', 'EDPSciences'),
                                        ('a', subject)])
        keywords = self._get_keywords()
        for keyword in keywords:
            record_add_field(rec, '653', ind1='1', subfields=[('a', keyword),
                                                              ('9', 'author')])
        journal, volume, issue, year, date, doi, page,\
            fpage, lpage = self._get_publication_information()
        astronomy_journals = ['EAS Publ.Ser.', 'Astron.Astrophys.']
        if journal in astronomy_journals:
            record_add_field(rec, '650', ind1='1', ind2='7',
                             subfields=[('2', 'INSPIRE'),
                                        ('a', 'Astrophysics')])
        if date:
            record_add_field(rec, '260', subfields=[('c', date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        abstract = self._get_abstract()
        abstract = self._format_abstract(abstract)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'EDPSciences')])
        license, license_type, license_url = self._get_license()
        subfields = []
        if license:
            subfields.append(('a', license))
        if license_url:
            subfields.append(('u', license_url))
        if subfields:
            record_add_field(rec, '540', subfields=subfields)
        if license_type == 'open-access':
            self._attach_fulltext(rec, doi)
        number_of_pages = self._get_page_count()
        if number_of_pages:
            record_add_field(rec, '300', subfields=[('a', number_of_pages)])
        c_holder, c_year, c_statement = self._get_copyright()
        if c_holder and c_year:
            record_add_field(rec, '542', subfields=[('d', c_holder),
                                                    ('g', c_year),
                                                    ('e', 'Article')])
        elif c_statement:
            record_add_field(rec, '542', subfields=[('f', c_statement),
                                                    ('e', 'Article')])
        subfields = []
        if journal:
            subfields.append(('p', journal))
        if issue:
            subfields.append(('n', issue))
        if volume:
            subfields.append(('v', volume))
        if fpage and lpage:
            subfields.append(('c', '%s-%s' % (fpage,
                                              lpage)))
        elif page:
            subfields.append(('c', page))
        if year:
            subfields.append(('y', year))
        record_add_field(rec, '773', subfields=subfields)
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        conference = ''
        for tag in self.document.getElementsByTagName('conference'):
            conference = xml_to_text(tag)
        if conference:
            record_add_field(rec, '980', subfields=[('a', 'ConferencePaper')])
            record_add_field(rec, '500', subfields=[('a', conference)])
        self._add_references(rec, ref_extract_callback)
        self._add_authors(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

    def get_record_rich(self, filename, ref_extract_callback=None):
        """
        Gets the Marc xml of the files in xaml_rich directory

        :param fileName: the name of the file to parse.
        :type fileName: string

        :returns: a string with the marc xml version of the file.
        """
        self.document = parse(filename)
        rec = create_record()
        articles = self.document.getElementsByTagName('ArticleID')
        for article in articles:
            article_type = article.getAttribute('Type')
            if not article_type == 'Article':
                return ''
            doi = get_value_in_tag(self.document, 'DOI')
            date = ''
            for tag in self.document.getElementsByTagName('Accepted'):
                year = get_value_in_tag(tag, 'Year')
                month = get_value_in_tag(tag, 'Month').zfill(2)
                day = get_value_in_tag(tag, 'Day').zfill(2)
                date = "%s-%s-%s" % (year, month, day)
            if not date:
                for tag in self.document.getElementsByTagName('OnlineDate'):
                    year = get_value_in_tag(tag, 'Year')
                    month = get_value_in_tag(tag, 'Month').zfill(2)
                    day = get_value_in_tag(tag, 'Day').zfill(2)
                    date = "%s-%s-%s" % (year, month, day)
            first_page = get_value_in_tag(article, 'FirstPage')
            last_page = get_value_in_tag(article, 'LastPage')
            subjects = article.getElementsByTagName('Keyword')
            subjects = map(xml_to_text, subjects)
            subject = ', '.join(subjects)
            copyright_statement = get_value_in_tag(article, 'Copyright')
        journal = get_value_in_tag(self.document, 'JournalTitle')
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        issues = self.document.getElementsByTagName('IssueID')
        for issue in issues:
            volume += get_value_in_tag(issue, 'Volume')
            year = get_value_in_tag(issue, 'Year')
        title = get_value_in_tag(self.document, 'Title')
        authors = self.document.getElementsByTagName('Author')
        affiliations = self.document.getElementsByTagName('Affiliation')

        def affiliation_pair(a):
            return a.getAttribute('ID'), get_value_in_tag(
                a, 'UnstructuredAffiliation'
            )

        affiliations = map(affiliation_pair, affiliations)
        affiliations = dict(affiliations)

        def author_pair(a):
            surname = get_value_in_tag(a, 'LastName')
            first_name = get_value_in_tag(a, 'FirstName')
            middle_name = get_value_in_tag(a, 'MiddleName')
            if middle_name:
                name = '%s, %s %s' % (surname, first_name, middle_name)
            else:
                name = '%s, %s' % (surname, first_name)
            try:
                affid = a.getElementsByTagName(
                    'AffiliationID'
                )[0].getAttribute('Label')
                affiliation = affiliations[affid]
            except IndexError:
                affiliation = ''
            except KeyError:
                affiliation = ''
            return name, affiliation

        authors = map(author_pair, authors)
        abstract = get_value_in_tag(self.document, 'Abstract')
        references = self.document.getElementsByTagName('Bibliomixed')

        for reference in references:
            subfields = []
            label = reference.getAttribute('N')
            if label:
                subfields.append(('o', label))
            bibliosets = reference.getElementsByTagName('Biblioset')
            for tag in bibliosets:
                ref_year = get_value_in_tag(tag, 'Date')
                ref_journal = get_value_in_tag(tag, 'JournalShortTitle')
                ref_journal, ref_volume = fix_journal_name(
                    ref_journal, self.journal_mappings
                )
                ref_volume += get_value_in_tag(tag, 'Volume')
                ref_page = get_value_in_tag(tag, 'ArtPageNums')
                if ref_year:
                    subfields.append(('y', ref_year))
                if ref_journal and ref_volume and ref_page:
                    subfields.append(('s', '%s,%s,%s' % (ref_journal,
                                                         ref_volume,
                                                         ref_page)))
                reference.removeChild(tag)
            text_ref = xml_to_text(reference)
            if ref_extract_callback:
                ref_xml = ref_extract_callback(text_ref)
                dom = parseString(ref_xml)
                fields = dom.getElementsByTagName("datafield")[0]
                fields = fields.getElementsByTagName("subfield")
                if fields:
                    subfields.append(('9', 'refextract'))
                for field in fields:
                    data = field.firstChild.data
                    code = field.getAttribute("code")
                    if code == 'm' and bibliosets:
                        continue
                    else:
                        subfields.append((code, data))
            else:
                subfields.append(('m', text_ref))
            if subfields:
                record_add_field(rec, '999', ind1='C', ind2='5',
                                 subfields=subfields)

        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        if date:
            record_add_field(rec, '260', subfields=[('c', date),
                                                    ('t', 'published')])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'EDPSciences')])
        first_author = True
        for author in authors:
            if first_author:
                subfields = [('a', author[0])]
                if author[1]:
                    subfields.append(('v', author[1]))
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                subfields = [('a', author[0])]
                if author[1]:
                    subfields.append(('v', author[1]))
                record_add_field(rec, '700', subfields=subfields)
        subfields = []
        if journal and volume and first_page:
            subfields.append(('s', "%s,%s,%s" % (journal,
                                                 volume,
                                                 first_page)))
        if first_page and last_page:
            try:
                nuber_of_pages = int(last_page) - int(first_page)
                record_add_field(rec, '300',
                                 subfields=[('a', str(nuber_of_pages))])
            except ValueError:
                pass
            subfields.append(('c', '%s-%s' % (first_page,
                                              last_page)))
        if year:
            subfields.append(('y', year))
        record_add_field(rec, '773', subfields=subfields)
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        if copyright_statement:
            record_add_field(rec, '542',
                             subfields=[('f', copyright_statement)])
        if subject:
            record_add_field(rec, '650', ind1='1', ind2='7',
                             subfields=[('2', 'EDPSciences'),
                                        ('a', subject)])
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

    def _attach_fulltext(self, rec, doi):
        url = 'http://dx.doi.org/' + doi
        page = requests.get(url)
        #url after redirect
        url = page.url
        page = page.text
        parsed_uri = urlparse(url)
        domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        page = BeautifulSoup(page)
        try:
            if 'epjconf' in doi:
                div = page.body.find('div', attrs={'id': 'header'})
            else:
                div = page.body.find('div', attrs={
                    'class': 'module_background files'
                })
            links = div.findAll('a')
        except AttributeError:
            return
        for pdf in links:
            if pdf['href'].endswith('pdf'):
                link_to_pdf = domain + pdf['href']
                record_add_field(rec, '856', ind1='4',
                                 subfields=[('u', link_to_pdf),
                                            ('y', 'EDP Sciences server')])
                out_folder = join(CFG_EDPSCIENCE_OUT_FOLDER,
                                  "fulltexts")
                try:
                    makedirs(out_folder)
                    filename = join(out_folder,
                                    link_to_pdf.split('/')[-1])
                except (IOError, OSError):
                    # Problem creating folder
                    filename = None

                filename = download_file(from_url=link_to_pdf,
                                         to_filename=filename,
                                         retry_count=5)
                record_add_field(rec, 'FFT',
                                 subfields=[('a', filename),
                                            ('t', 'INSPIRE-PUBLIC'),
                                            ('d', 'Fulltext')])


if __name__ == '__main__':
    filename = sys.argv[1]
    edp = EDPSciencesPackage()
    if 'xml_rich' in filename:
        print(edp.get_record_rich(filename))
    else:
        print(edp.get_record(filename))
