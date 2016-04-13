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

from __future__ import print_function

import sys

from datetime import date, datetime

from harvestingkit.utils import (fix_journal_name,
                                 collapse_initials)
from harvestingkit.bibrecord import record_add_field
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text,
                                         get_attribute_in_tag,
                                         get_inner_xml)


class JatsPackage(object):

    """Generic package to convert JATS/XML formatted articles."""

    def __init__(self, journal_mappings={}):
        """Create a JatsPackage."""
        self.journal_mappings = journal_mappings
        self.document = None

    def _get_journal(self):
        try:
            title = get_value_in_tag(self.document, 'abbrev-journal-title')
            if not title:
                title = get_value_in_tag(self.document, 'journal-title')
            return title.strip()
        except Exception:
            print("Can't find journal-title", file=sys.stderr)
            return ''

    def _get_abstract(self):
        for tag in self.document.getElementsByTagName('abstract'):
            return get_inner_xml(tag)

    def _get_title(self):
        try:
            notes = []
            for tag in self.document.getElementsByTagName('article-title'):
                for note in tag.getElementsByTagName('xref'):
                    if note.getAttribute('ref-type') == 'fn':
                        tag.removeChild(note)
                        notes.append(note.getAttribute('rid'))
                return get_inner_xml(tag), get_value_in_tag(self.document, 'subtitle'), notes
        except Exception:
            print("Can't find title", file=sys.stderr)
            return '', '', ''

    def _get_doi(self):
        try:
            for tag in self.document.getElementsByTagName('article-id'):
                if tag.getAttribute('pub-id-type') == 'doi':
                    return tag.firstChild.data
        except Exception:
            print("Can't find doi", file=sys.stderr)
            return ''

    def _get_affiliations(self):
        affiliations = {}
        for tag in self.document.getElementsByTagName('aff'):
            aid = tag.getAttribute('id')
            affiliation = xml_to_text(tag)
            if affiliation:
                #removes the label
                try:
                    int(affiliation.split()[0])
                    affiliation = ' '.join(affiliation.split()[1:])
                except ValueError:
                    pass
            affiliations[aid] = affiliation
        return affiliations

    def _get_author_emails(self):
        author_emails = {}
        for tag in self.document.getElementsByTagName('author-notes'):
            email_elements = tag.getElementsByTagName('corresp')
            email_elements += tag.getElementsByTagName('fn')
            for tg in email_elements:
                nid = tg.getAttribute('id')
                email = xml_to_text(tg)
                email = email.replace(';', '')
                #removes the label
                if email.split() > 1:
                    emails = email.split()[1:]
                valid_emails = []
                for email in emails:
                    if '@' in email and '.' in email:
                        valid_emails.append(email)
                author_emails[nid] = valid_emails
        return author_emails

    def _get_authors(self):
        authors = []
        for contrib in self.document.getElementsByTagName('contrib'):
            # Springer puts colaborations in additional "contrib" tag so to
            # avoid having fake author with all affiliations we skip "contrib"
            # tag with "contrib" subtags.
            if contrib.getElementsByTagName('contrib'):
                continue
            if contrib.getAttribute('contrib-type') == 'author':
                surname = get_value_in_tag(contrib, 'surname')
                given_names = get_value_in_tag(contrib, 'given-names')
                given_names = collapse_initials(given_names)
                name = '%s, %s' % (surname, given_names)
                affiliations = []
                corresp = []
                for tag in contrib.getElementsByTagName('xref'):
                    if tag.getAttribute('ref-type') == 'aff':
                        for rid in tag.getAttribute('rid').split():
                            if rid.lower().startswith('a'):
                                affiliations.append(rid)
                            elif rid.lower().startswith('n'):
                                corresp.append(rid)
                    elif tag.getAttribute('ref-type') == 'corresp' or\
                            tag.getAttribute('ref-type') == 'author-notes':
                        for rid in tag.getAttribute('rid').split():
                            corresp.append(rid)
                authors.append((name, affiliations, corresp))
        return authors

    def _get_license(self):
        license = ''
        license_type = ''
        license_url = ''
        for tag in self.document.getElementsByTagName('license'):
            license = get_value_in_tag(tag, 'ext-link')
            license_type = tag.getAttribute('license-type')
            license_url = get_attribute_in_tag(tag, 'ext-link', 'xlink:href')
        if license_url:
            license_url = license_url[0]
        return license, license_type, license_url

    def _get_page_count(self):
        try:
            return get_attribute_in_tag(self.document, 'page-count', 'count')[0]
        except IndexError:
            print("Can't find page count", file=sys.stderr)
            return ''

    def _get_copyright(self):
        try:
            copyright_holder = get_value_in_tag(self.document, 'copyright-holder')
            copyright_year = get_value_in_tag(self.document, 'copyright-year')
            copyright_statement = get_value_in_tag(self.document, 'copyright-statement')
            return copyright_holder, copyright_year, copyright_statement
        except Exception:
            print("Can't find copyright", file=sys.stderr)
            return '', '', ''

    def _get_pacscodes(self):
        pacscodes = []
        for tag in self.document.getElementsByTagName('kwd-group'):
            if tag.getAttribute('kwd-group-type') == 'pacs':
                for code in tag.getElementsByTagName('kwd'):
                    pacscodes.append(xml_to_text(code))
        return pacscodes

    def _get_date(self):
        final = ''
        epub_date = ''
        ppub_date = ''
        for dateTag in self.document.getElementsByTagName('pub-date'):
            if dateTag.getAttribute('pub-type') == 'final':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    final = str(date(year, month, day))
                except ValueError:
                    pass
            if dateTag.getAttribute('pub-type') == 'epub':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    epub_date = str(date(year, month, day))
                except ValueError:
                    epub_date = dateTag.getAttribute('iso-8601-date')
            elif dateTag.getAttribute('pub-type') == 'ppub':
                try:
                    day = int(get_value_in_tag(dateTag, 'day'))
                    month = int(get_value_in_tag(dateTag, 'month'))
                    year = int(get_value_in_tag(dateTag, 'year'))
                    ppub_date = str(date(year, month, day))
                except ValueError:
                    ppub_date = dateTag.getAttribute('iso-8601-date')
        if final:
            return final
        elif epub_date:
            return epub_date
        elif ppub_date:
            return ppub_date
        else:
            print("Can't find publication date", file=sys.stderr)
            return datetime.now().strftime("%Y-%m-%d")

    def _get_publisher(self):
        try:
            return get_value_in_tag(self.document, 'publisher')
        except Exception:
            print("Can't find publisher", file=sys.stderr)
            return ''

    def _get_subject(self):
        subjects = []
        for tag in self.document.getElementsByTagName('subj-group'):
            if tag.getAttribute('subj-group-type') == 'toc-minor' or \
                    tag.getAttribute('subj-group-type') == 'section':
                for subject in tag.getElementsByTagName('subject'):
                    subjects.append(xml_to_text(subject))
        return ', '.join(subjects)

    def _get_publication_information(self):
        journal = self._get_journal()
        date = self._get_date()
        doi = self._get_doi()
        issue = get_value_in_tag(self.document, 'issue')
        journal, volume = fix_journal_name(journal, self.journal_mappings)
        volume += get_value_in_tag(self.document, 'volume')
        page = get_value_in_tag(self.document, 'elocation-id')
        fpage = get_value_in_tag(self.document, 'fpage')
        lpage = get_value_in_tag(self.document, 'lpage')
        year = date[:4]
        return (journal, volume, issue, year, date, doi, page, fpage, lpage)

    def _get_keywords(self):
        keywords = []
        for tag in self.document.getElementsByTagName('kwd-group'):
            if tag.getAttribute('kwd-group-type') != 'pacs':
                for kwd in tag.getElementsByTagName('kwd'):
                    keywords.append(xml_to_text(kwd))
        return keywords

    def _add_authors(self, rec):
        authors = self._get_authors()
        affiliations = self._get_affiliations()
        author_emails = self._get_author_emails()
        first_author = True
        for author in authors:
            subfields = [('a', author[0])]
            if author[1]:
                for aff in author[1]:
                    subfields.append(('v', affiliations[aff]))
            if author[2]:
                for note in author[2]:
                    for email in author_emails.get(note, []):
                        if email:
                            subfields.append(('m', email))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)

    def _get_article_type(self):
        article_type = get_attribute_in_tag(self.document, 'article', 'article-type')
        if article_type:
            article_type = article_type[0]
        return article_type
