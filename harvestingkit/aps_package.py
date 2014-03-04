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
import xml.dom.minidom
import re

from invenio.refextract_kbs import get_kbs
from datetime import datetime
from xml.dom.minidom import parse
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
            affiliations[aid] = institution
        for tag in self.document.getElementsByTagName('contrib'):
            if tag.getAttribute('contrib-type') == 'author':
                rid = ''
                for aff in tag.getElementsByTagName('xref'):
                    if aff.getAttribute('ref-type') == 'aff':
                        rid = aff.getAttribute('rid')
                given_name = get_value_in_tag(tag, 'given-names')
                surname = get_value_in_tag(tag, 'surname')
                name = "%s, %s" % (surname, given_name)
                try:
                    authors.append((name, affiliations[rid]))
                except KeyError:
                    authors.append((name, ''))
        return authors

    def _get_copyright(self):
        try:
            return get_value_in_tag(self.document, 'copyright-statement')
        except Exception, err:
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

    def _get_issn(self):
        epub_issn = ''
        ppub_issn = ''
        for issn in self.document.getElementsByTagName('issn'):
            if issn.getAttribute('pub-type') == 'epub':
                epub_issn = issn.firstChild.data
            elif issn.getAttribute('pub-type') == 'ppub':
                ppub_issn = issn.firstChild.data
        if epub_issn:
            return epub_issn
        else:
            return ppub_issn

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'publisher')
        except Exception:
            print >> sys.stderr, "Can't find publisher"
            return ''

    def _get_publition_information(self):
        journal = self._get_journal()
        date = self._get_date()
        issn = self._get_issn()
        doi = self._get_doi()
        jounal, volume = self._fix_journal_name(journal)
        volume += get_value_in_tag(self.document, 'volume')
        issue = get_value_in_tag(self.document, 'issue')
        year = get_value_in_tag(self.document, 'copyright-year')
        return (journal, issn, volume, issue, year, date, doi)

    def _fix_journal_name(self, journal):
        """ Converts journal name to Inspire's short form """
        if not journal:
            return '', ''
        volume = ''
        if journal[-1] <= 'Z' and journal[-1] >= 'A':
            volume += journal[-1]
            journal = journal[:-1]
            try:
                journal = self.journal_mappings[journal.upper()].strip()
            except KeyError:
                try:
                    journal = self.journal_mappings[journal].strip()
                except KeyError:
                    pass
        journal = journal.replace('. ', '.')
        return journal, volume

    def _get_reference(self, ref):
        """ Retrieves the data for a reference """
        label = get_value_in_tag(ref, 'label')
        label = re.sub('\D', '', label)
        for innerref in ref.getElementsByTagName('mixed-citation'):
            doi = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    doi = tag.firstChild.data
            authors = []
            collaboration = get_value_in_tag(innerref, 'collab')
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
            journal, volume = self._fix_journal_name(journal)
            volume += get_value_in_tag(innerref, 'volume')
            page = get_value_in_tag(innerref, 'page-range')
            year = get_value_in_tag(innerref, 'year')
            
            institution = get_value_in_tag(innerref, 'institution')
            report_no = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'other':
                    report_no = tag.firstChild.data
            arxiv = ''
            for tag in innerref.getElementsByTagName('pub-id'):
                if tag.getAttribute('pub-id-type') == 'arxiv':
                    arxiv = tag.firstChild.data
            publisher = get_value_in_tag(innerref, 'publisher-name')
            yield doi, authors, collaboration, journal, volume, page, year, label, arxiv, publisher, institution, report_no

    def _add_reference(self, rec, ref):
        """ Adds the journal-type references to the record """
        for doi, authors, collaboration, journal, volume, page, year, label, arxiv, publisher, institution, report_no in self._get_reference(ref):
            subfields = []
            if doi:
                subfields.append(('a', doi))
            for author in authors:
                subfields.append(('h', author))
            if volume:
                subfields.append(('s', journal + "," + volume))
            elif journal:
                subfields.append(('s', journal))
            if year:
                subfields.append(('y', year))
            if report_no:
                subfields.append(('s', "Technical Report No." + report_no))
            if collaboration:
                subfields.append(('c', collaboration))
            if institution:
                subfields.append(('m', institution))
            if publisher:
                subfields.append(('m', publisher))
            if page:
                subfields.append(('p', page))
            if arxiv:
                subfields.append(('r', arxiv))
            if label:
                subfields.append(('o', label))
            if not subfields:
                try:
                    try:
                        r = ref.getElementsByTagName('mixed-citation')[0]
                        text = xml_to_text(r)
                        label = text.split()[0]
                        text = " ".join(text.split()[1:])
                        subfields.append(('s', text))
                        record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)                    
                except IndexError:
                    try:
                        r = ref.getElementsByTagName('note')[0]
                        subfields.append(('s', xml_to_text(r)))
                        record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
                    except IndexError:
                        subfields.append(('s', xml_to_text(ref)))
                        record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)
            else:                
                record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

    def _add_references(self, rec):
        """ Adds the references on the record """        
        for ref in self.document.getElementsByTagName('ref'):
            self._add_reference(rec,ref)

    def get_record(self, xml_file):
        """ Reads a xml file in JATS format and returns
            a xml string in marc format """
        self.document = parse(xml_file)
        rec = {}
        title = self._get_title()
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, issn, volume, issue, year, start_date, doi = self._get_publition_information()
        if start_date:
            record_add_field(rec, '260', subfields=[('c', start_date)])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
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
            record_add_field(rec, '520', subfields=[('a', abstract), ('9', 'Elsevier')])
        copyright = self._get_copyright()
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        record_add_field(rec, '773', subfields=[('p', journal), ('v', volume), ('n', issue), ('y', year)])
        record_add_field(rec, '980', subfields=[('a', 'HEP')])
        record_add_field(rec, '980', subfields=[('a', 'Citeable')])
        self._add_references(rec)
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            sys.stderr.write("Found a bad char in the file for the article " + doi)
            return ""


def main(args):
    if len(args) != 1:
        print "usage: python aps_package.py <filename>"
        sys.exit()
    a = ApsPackage()
    print a.get_record(args[0])

if __name__ == '__main__':
    main(sys.argv[1:])
