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
import sys
import re

from invenio.refextract_kbs import get_kbs
from datetime import datetime
from xml.dom.minidom import parse
from harvestingkit.utils import fix_journal_name, collapse_initials
from harvestingkit.minidom_utils import get_value_in_tag, xml_to_text
from invenio.bibrecord import record_add_field, record_xml_output


class ApsPackage(object):
    """
    This class is specialized in parsing an APS harvested file in JATS format
    and creating a Inspire-compatible bibupload containing the original
    XML and every possible metadata filled in.
    """
    def __init__(self):
        try:
            self.journal_mappings = get_kbs()['journals'][1]
        except KeyError:
            self.journal_mappings = {}

    def _get_journal(self):
        try:
            title = get_value_in_tag(self.document, 'abbrev-journal-title')
            if not title:
                title = get_value_in_tag(self.document, 'journal-title')
            try:
                title = self.journal_mappings[title.upper()]
            except KeyError:
                pass
            title = title.replace('. ', '.')
            return title
        except Exception:
            print >> sys.stderr, "Can't find journal-title"
            return ''

    def _get_abstract(self):
        try:
            return get_value_in_tag(self.document, 'abstract')
        except Exception:
            print >> sys.stderr, "Can't find abstract"
            return ''

    def _get_title(self):
        try:
            return get_value_in_tag(self.document, 'article-title')
        except Exception:
            print >> sys.stderr, "Can't find title"
            return ''

    def _get_doi(self):
        try:
            for tag in self.document.getElementsByTagName('article-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    return tag.firstChild.data
        except Exception:
            print >> sys.stderr, "Can't find doi"
            return ''

    def _get_authors(self):
        authors = []
        affiliations = {}
        for tag in self.document.getElementsByTagName('aff'):
            aid = tag.getAttribute('id')
            institution = get_value_in_tag(tag, 'institution')
            affiliation = xml_to_text(tag)
            affiliation = ' '.join(affiliation.split()[1:])
            affiliations[aid] = affiliation
        for tag in self.document.getElementsByTagName('contrib'):
            if tag.getAttribute('contrib-type') == 'author':
                rid = ''
                for aff in tag.getElementsByTagName('xref'):
                    if aff.getAttribute('ref-type') == 'aff':
                        rid = aff.getAttribute('rid')
                    if len(rid.split()) > 1:
                        rid = rid.split()[0]
                given_names = get_value_in_tag(tag, 'given-names')
                given_names = collapse_initials(given_names)
                surname = get_value_in_tag(tag, 'surname')
                name = "%s, %s" % (surname, given_names)
                try:
                    authors.append((name, affiliations[rid]))
                except KeyError:
                    authors.append((name, ''))
        return authors

    def _get_copyright(self):
        try:
            return get_value_in_tag(self.document, 'copyright-statement')
        except Exception:
            print >> sys.stderr, "Can't find copyright"
            return ''

    def _get_date(self):
        epub_date = ''
        ppub_date = ''
        for date in self.document.getElementsByTagName('pub-date'):
            if date.getAttribute('pub-type') == 'epub':
                epub_date = date.getAttribute('iso-8601-date')
            elif date.getAttribute('pub-type') == 'ppub':
                ppub_date = date.getAttribute('iso-8601-date')
        if epub_date:
            return epub_date
        elif ppub_date:
            return ppub_date
        else:
            print >> sys.stderr, "Can't find publication date"
            return datetime.now().strftime("%Y-%m-%d")

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'publisher')
        except Exception:
            print >> sys.stderr, "Can't find publisher"
            return ''

    def _get_publition_information(self):
        journal = self._get_journal()
        date = self._get_date()
        doi = self._get_doi()
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        article_id = get_value_in_tag(self.document, 'elocation-id')
        volume += get_value_in_tag(self.document, 'volume')
        issue = get_value_in_tag(self.document, 'issue')
        year = get_value_in_tag(self.document, 'copyright-year')
        return (journal, volume, issue, year, date, doi, article_id)

    def _get_reference(self, ref):
        """ Retrieves the data for a reference """
        label = get_value_in_tag(ref, 'label')
        label = re.sub('\D', '', label)
        for innerref in ref.getElementsByTagName('mixed-citation'):
            ref_type = innerref.getAttribute('publication-type')
            institution = get_value_in_tag(innerref, 'institution')
            report_no = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'other':
                    report_no = tag.firstChild.data
            doi = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    doi = tag.firstChild.data
            collaboration = get_value_in_tag(innerref, 'collab')
            authors = []
            try:
                authors_xml = innerref.getElementsByTagName('person-group')[0]
                for author in authors_xml.getElementsByTagName('string-name'):
                    try:
                        authors.append(author.firstChild.data)
                    except AttributeError:
                        pass
            except IndexError:
                pass
            journal = get_value_in_tag(innerref, 'source')
            journal, volume = fix_journal_name(journal, self.journal_mappings)
            volume += get_value_in_tag(innerref, 'volume')
            if journal == 'J.High Energy Phys.' or journal == 'JHEP':
                issue = get_value_in_tag(innerref, 'issue')
                volume = volume[2:]+issue
                journal = 'JHEP'
            page = get_value_in_tag(innerref, 'page-range')
            year = get_value_in_tag(innerref, 'year')
            external_link = get_value_in_tag(innerref, 'ext-link')
            arxiv = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'arxiv':
                    arxiv = tag.firstChild.data
            publisher = get_value_in_tag(innerref, 'publisher-name')
            unstructured_text = []
            for child in innerref.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    text = child.nodeValue.strip()
                    text = re.sub('[\[\](.;)]', '', text).strip()
                    if text.startswith(','):
                        text = text[1:].strip()
                    if text.endswith('Report No'):
                        text = institution + " " + text
                        institution = ''
                        text = text.strip()
                    elif text.endswith(' ed'):
                        text += '.'
                    elif text.endswith('PhD thesis,'):
                        if institution:
                            text += ' ' + institution
                            institution = ''
                        else:
                            text = text[:-1]
                    elif text.startswith('Seminar,'):
                        article_title = get_value_in_tag(innerref, 'article-title')
                        text = institution + " Seminar, \"" + article_title + "\""
                        institution = ''
                    elif text == u'\u201d':
                        text = ''
                    ignore_text = ['in', 'pp', 'edited by', 'Vol']
                    if len(text) > 1 and text not in ignore_text\
                            and not (text.isdigit() or text[:-1].isdigit()):
                        unstructured_text.append(text)
            if unstructured_text:
                unstructured_text = " ".join(unstructured_text)
            yield ref_type, doi, authors, collaboration, journal, volume, page, year,\
                label, arxiv, publisher, institution, unstructured_text, external_link, report_no

    def _add_references(self, rec):
        """ Adds the reference to the record """
        for ref in self.document.getElementsByTagName('ref'):
            for ref_type, doi, authors, collaboration, journal, volume, page, year,\
                    label, arxiv, publisher, institution, unstructured_text,\
                    external_link, report_no in self._get_reference(ref):
                subfields = []
                if doi:
                    subfields.append(('a', doi))
                for author in authors:
                    subfields.append(('h', author))
                if year:
                    subfields.append(('y', year))
                if unstructured_text:
                    if page and unstructured_text.endswith('pp'):
                        subfields.append(('m', unstructured_text + ' ' + page))
                    else:
                        subfields.append(('m', unstructured_text))
                if collaboration:
                    subfields.append(('c', collaboration))
                if institution:
                    subfields.append(('m', institution))
                if publisher:
                    subfields.append(('p', publisher))
                if arxiv:
                    subfields.append(('r', arxiv))
                if report_no:
                    subfields.append(('r', report_no))
                if external_link:
                    subfields.append(('u', external_link))
                if label:
                    subfields.append(('o', label))
                if ref_type:
                    subfields.append(('d', ref_type))
                if ref_type == 'book':
                    if journal:
                        subfields.append(('t', journal))
                else:
                    if volume and page:
                        subfields.append(('s', journal + "," + volume + "," + page))
                    elif volume:
                        subfields.append(('s', journal + "," + volume))
                    elif journal:
                        subfields.append(('s', journal))
                if not subfields:
                    #misc-type references
                    try:
                        r = ref.getElementsByTagName('mixed-citation')[0]
                        text = xml_to_text(r)
                        label = text.split()[0]
                        text = " ".join(text.split()[1:])
                        subfields.append(('s', text))
                        record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                    except IndexError:
                        #references without 'mixed-citation' tag
                        try:
                            r = ref.getElementsByTagName('note')[0]
                            subfields.append(('s', xml_to_text(r)))
                            record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                        except IndexError:
                            #references without 'note' tag
                            subfields.append(('s', xml_to_text(ref)))
                            record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                else:
                    record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

    def get_record(self, xml_file):
        """ Reads a xml file in JATS format and returns
            a xml string in marc format """
        self.document = parse(xml_file)
        rec = {}
        title = self._get_title()
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, volume, issue, year, start_date, doi,\
            article_id = self._get_publition_information()
        if start_date:
            record_add_field(rec, '260', subfields=[('c', start_date)])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        authors = self._get_authors()
        first_author = True
        for author in authors:
            subfields = [('a', author[0]), ('v', author[1])]
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        abstract = self._get_abstract()
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'APS')])
        copyrightt = self._get_copyright()
        if copyrightt:
            year = ''
            if copyrightt.startswith('©'):
                year = copyrightt[2:].strip()
                year = year.split()[0]
            if year.isdigit():
                copyrightt = copyrightt[2:].strip()
                copyrightt = " ".join(copyrightt.split()[1:])
                record_add_field(rec, '542', subfields=[('d', copyrightt),
                                                        ('g', year),
                                                        ('3', 'Article')])
            else:
                year = start_date[:4]
                record_add_field(rec, '542', subfields=[('f', copyrightt),
                                                        ('g', year),
                                                        ('3', 'Article')])
        record_add_field(rec, '773', subfields=[('p', journal),
                                                ('v', volume),
                                                ('n', issue),
                                                ('y', year),
                                                ('c', article_id)])
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        record_add_field(rec, '980', subfields=[('a', 'Citeable')])
        record_add_field(rec, '980', subfields=[('a', 'Published')])
        self._add_references(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            sys.stderr.write("""Found a bad char in the file
                                for the article """ + doi)
            return ""


def main(args):
    if len(args) != 1:
        print "usage: python aps_package.py <filename>"
        sys.exit()
    a = ApsPackage()
    print a.get_record(args[0])

if __name__ == '__main__':
    main(sys.argv[1:])
