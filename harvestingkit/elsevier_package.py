# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2013, 2014 CERN.
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

from __future__ import print_function

import re
import sys
import traceback
import time
import requests
import xml.dom.minidom

from bs4 import BeautifulSoup
from os import listdir, rename, fdopen
from os.path import join, exists, walk
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from zipfile import ZipFile
from xml.dom.minidom import parse

from invenio.refextract_kbs import get_kbs
from invenio.refextract_api import extract_references_from_string_xml
from invenio.errorlib import register_exception
from invenio.bibrecord import record_add_field, record_xml_output
from invenio.config import CFG_TMPSHAREDDIR
from invenio.shellutils import run_shell_command
from invenio.bibtask import task_low_level_submission
from .scoap3utils import (create_logger,
                          MissingFFTError,
                          FileTypeError)
from .contrast_out_utils import find_package_name
from .minidom_utils import (get_value_in_tag,
                            xml_to_text,
                            format_arxiv_id)
from .config import CFG_DTDS_PATH as CFG_SCOAP3DTDS_PATH
from .utils import fix_journal_name, collapse_initials

CFG_ELSEVIER_ART501_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art501.zip')
CFG_ELSEVIER_ART510_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art510.zip')
CFG_ELSEVIER_ART520_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art520.zip')
CFG_ELSEVIER_SI510_PATH = join(CFG_SCOAP3DTDS_PATH, 'si510.zip')
CFG_ELSEVIER_SI520_PATH = join(CFG_SCOAP3DTDS_PATH, 'si520.zip')
CFG_ELSEVIER_JID_MAP = {'PLB': 'Physics letters B',
                        'NUPHB': 'Nuclear Physics B',
                        'CEMGE': 'Chemical Geology',
                        'SOLMAT': 'Solar Energy Materials & Solar Cells',
                        'APCATB': 'Applied Catalysis B: Environmental',
                        'NUMA': 'Journal of Nuclear Materials'}


class ElsevierPackage(object):

    """
    This class is specialized in parsing an Elsevier package
    and creating a SCOAP3-compatible bibupload containing the original
    PDF, XML, and every possible metadata filled in.

    @param package_name: the path to a tar.gz file to expand and parse
    @param path: the actual path of an already expanded package.

    @note: either C{package_name} or C{path} don't have to be passed to the
    constructor, in this case the Elsevier server will be harvested.
    """

    def __init__(self, package_name=None, path=None,
                 run_localy=False, CONSYN=False):
        self.CONSYN = CONSYN
        self.package_name = package_name
        self.path = path
        self.found_articles = []
        self._found_issues = []
        self.logger = create_logger("Elsevier")
        if run_localy:
            from invenio.contrast_out import ContrastOutConnector
            self.conn = ContrastOutConnector(self.logger)
            self.conn.run(run_localy)
        else:
            if not path and package_name:
                self.logger.info("Got package: %s" % (package_name,))
                self._extract_package()
            elif not path and not package_name:
                from invenio.contrast_out import ContrastOutConnector
                self.conn = ContrastOutConnector(self.logger)
                self.conn.run()
        if CONSYN:
            self._build_journal_mappings()
        else:
            self._crawl_elsevier_and_find_main_xml()
            self._crawl_elsevier_and_find_issue_xml()
            self._build_doi_mapping()

    def _build_journal_mappings(self):
        try:
            self.journal_mappings = get_kbs()['journals'][1]
        except KeyError:
            self.journal_mappings = {}
            return

    def _extract_package(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path = mkdtemp(prefix="scoap3_package_", dir=CFG_TMPSHAREDDIR)
        self.logger.debug("Extracting package: %s" % (self.package_name,))
        try:
            if ".tar" in self.package_name:
                TarFile.open(self.package_name).extractall(self.path)
            elif ".zip" in self.package_name:
                ZipFile(self.package_name).extractall(self.path)
            else:
                raise FileTypeError("It's not a TAR or ZIP archive.")
        except Exception, err:
            register_exception(alert_admin=True,
                               prefix="Elsevier error extracting package.")
            self.logger.error("Error extraction package file: %s %s"
                              % (self.path, err))
            print("\nError extracting package file: %s %s" % (self.path, err))

    def _crawl_elsevier_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in agiven directory.
        """
        self.found_articles = []
        if not self.path and not self.package_name:
            for doc in self.conn.found_articles:
                dirname = doc['xml'].rstrip('/main.xml')
                try:
                    self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception, err:
                    register_exception()
                    print("ERROR: can't normalize %s: %s" % (dirname, err))
        else:
            def visit(dummy, dirname, names):
                if "main.xml" in names and "main.pdf" in names:
                    try:
                        self._normalize_article_dir_with_dtd(dirname)
                        self.found_articles.append(dirname)
                    except Exception, err:
                        register_exception()
                        print("ERROR: can't normalize %s: %s" % (dirname, err))
            walk(self.path, visit, None)

    def _crawl_elsevier_and_find_issue_xml(self):
        """
        Information about the current volume, issue, etc. is available
        in a file called issue.xml that is available in a higher directory.
        """
        self._found_issues = []
        if not self.path and not self.package_name:
            for issue in self.conn._get_issues():
                dirname = issue.rstrip('/issue.xml')
                try:
                    self._normalize_issue_dir_with_dtd(dirname)
                    self._found_issues.append(dirname)
                except Exception as err:
                    register_exception()
                    print("ERROR: can't normalize %s: %s" % (dirname, err))
        else:
            def visit(dummy, dirname, names):
                if "issue.xml" in names:
                    try:
                        self._normalize_issue_dir_with_dtd(dirname)
                        self._found_issues.append(dirname)
                    except Exception as err:
                        register_exception()
                        print("ERROR: can't normalize %s: %s"
                              % (dirname, err))
            walk(self.path, visit, None)

    def _normalize_issue_dir_with_dtd(self, path):
        """
        issue.xml from Elsevier assume the existence of a local DTD.
        This procedure install the DTDs next to the issue.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        if exists(join(path, 'resolved_issue.xml')):
            return
        if 'si510.dtd' in open(join(path, 'issue.xml')).read():
            ZipFile(CFG_ELSEVIER_SI510_PATH).extractall(path)
            for filename in listdir(join(path, 'si510')):
                rename(join(path, 'si510', filename), join(path, filename))
        elif 'si520.dtd' in open(join(path, 'issue.xml')).read():
            ZipFile(CFG_ELSEVIER_SI520_PATH).extractall(path)
            for filename in listdir(join(path, 'si520')):
                rename(join(path, 'si520', filename), join(path, filename))
        else:
            message = "It looks like the path " + path
            message += " does not contain an si510 or si520 issue.xml file"
            self.logger.error(message)
            raise ValueError(message)
        command = "xmllint --format --loaddtd " + join(path, 'issue.xml')
        command += " --output " + join(path, 'resolved_issue.xml')
        dummy, dummy, cmd_err = run_shell_command(command)
        if cmd_err:
            message = "Error in cleaning %s: %s" % (
                join(path, 'issue.xml'), cmd_err)
            self.logger.error(message)
            raise ValueError(message)

    def _normalize_article_dir_with_dtd(self, path):
        """
        main.xml from Elsevier assume the existence of a local DTD.
        This procedure install the DTDs next to the main.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        if exists(join(path, 'resolved_main.xml')):
            return
        if 'art520' in open(join(path, 'main.xml')).read():
            ZipFile(CFG_ELSEVIER_ART520_PATH).extractall(path)
            for filename in listdir(join(path, 'art520')):
                rename(join(path, 'art520', filename), join(path, filename))
        elif 'art501' in open(join(path, 'main.xml')).read():
            ZipFile(CFG_ELSEVIER_ART501_PATH).extractall(path)
            for filename in listdir(join(path, 'art501')):
                rename(join(path, 'art501', filename), join(path, filename))
        else:
            message = "It looks like the path " + path
            message += "does not contain an si520 or si501 main.xml file"
            self.logger.error(message)
            raise ValueError(message)
        command = "xmllint --format --loaddtd " + join(path, 'main.xml')
        command += " --output " + join(path, 'resolved_main.xml')
        dummy, dummy, cmd_err = run_shell_command(command)
        if cmd_err:
            message = "Error in cleaning %s: %s" % (
                join(path, 'main.xml'), cmd_err)
            self.logger.error(message)
            raise ValueError(message)

    def _add_references(self, xml_doc, rec):
        if self.CONSYN:
            for label, authors, doi, issue, page, title, volume, year,\
                    textref, ext_link, isjournal, comment, journal, publisher,\
                    editors, book_title in self.get_references(xml_doc):
                subfields = []
                if textref and not authors:
                    textref = textref.replace('\"', '\'')
                    ref_xml = extract_references_from_string_xml(textref)
                    dom = xml.dom.minidom.parseString(ref_xml)
                    fields = dom.getElementsByTagName("datafield")[0]
                    fields = fields.getElementsByTagName("subfield")
                    for field in fields:
                        data = field.firstChild.data
                        code = field.getAttribute("code")
                        if code == 's':
                            try:
                                journal = data.split(',')[0]
                                journal, vol = fix_journal_name(journal, self.journal_mappings)
                                vol += data.split(',')[1]
                                try:
                                    page = data.split(',')[2]
                                    journal = journal + "," + vol + "," + page
                                    subfields.append(('s', journal))
                                except IndexError:
                                    journal = journal + "," + vol
                                    subfields.append(('s', journal))
                            except IndexError:
                                subfields.append(('s', data))
                        else:
                            subfields.append((code, data))
                    if label:
                        label = re.sub("[\[\].)]", "", label)
                        subfields.append(('o', label))
                    if subfields:
                        record_add_field(rec,
                                         '999',
                                         ind1='C',
                                         ind2='5',
                                         subfields=subfields)
                elif isjournal:
                    if doi:
                        subfields.append(('a', doi))
                    for author in authors:
                        subfields.append(('h', author))
                    if title:
                        subfields.append(('t', title))
                    if journal:
                        journal, vol = fix_journal_name(journal, self.journal_mappings)
                        volume = vol + volume
                        if volume and page:
                            journal = journal + "," + volume + "," + page
                            subfields.append(('s', journal))
                        elif volume:
                            journal = journal + "," + volume
                            subfields.append(('s', journal))
                        else:
                            subfields.append(('s', journal))
                    if ext_link:
                        subfields.append(('r', ext_link))
                    if year:
                        subfields.append(('y', year))
                    if label:
                        label = re.sub("[\[\].)]", "", label)
                        subfields.append(('o', label))
                    if subfields:
                        record_add_field(rec,
                                         '999',
                                         ind1='C',
                                         ind2='5',
                                         subfields=subfields)
                else:
                    if doi:
                        subfields.append(('a', doi))
                    for author in authors:
                        subfields.append(('h', author))
                    if issue:
                        subfields.append(('n', issue))
                    if ext_link:
                        subfields.append(('r', ext_link))
                    if title:
                        subfields.append(('t', title))
                    elif textref:
                        subfields.append(('m', textref))
                    if publisher:
                        subfields.append(('p', publisher))
                    if volume:
                        subfields.append(('v', volume))
                    if year:
                        subfields.append(('y', year))
                    if comment:
                        subfields.append(('m', comment))
                    for editor in editors:
                        subfields.append(('e', editor))
                    if book_title:
                        subfields.append(('q', book_title))
                    if label:
                        label = re.sub("[\[\].)]", "", label)
                        subfields.append(('o', label))
                    if subfields:
                        record_add_field(rec,
                                         '999',
                                         ind1='C',
                                         ind2='5',
                                         subfields=subfields)
        else:
            for label, authors, doi, issue, page, title, volume, year,\
                    textref, ext_link in self.get_references(xml_doc):
                subfields = []
                if doi:
                    subfields.append(('a', doi))
                for author in authors:
                    subfields.append(('h', author))
                if issue:
                    subfields.append(('n', issue))
                if label:
                    subfields.append(('o', label))
                if page:
                    subfields.append(('p', page))
                if ext_link:
                    subfields.append(('r', ext_link))
                if title and volume and year and page:
                    subfields.append(
                        ('s', '%s %s (%s) %s' % (title, volume, year, page)))
                elif textref:
                    subfields.append(('m', textref))
                if title:
                    subfields.append(('t', title))
                if volume:
                    subfields.append(('v', volume))
                if year:
                    subfields.append(('y', year))
                if subfields:
                    record_add_field(
                        rec, '999', ind1='C', ind2='5', subfields=subfields)

    def _build_doi_mapping(self):
        self._dois = {}
        for path in self._found_issues:
            xml_doc = parse(open(join(path, "resolved_issue.xml")))
            jid = get_value_in_tag(xml_doc, "jid")
            journal = CFG_ELSEVIER_JID_MAP.get(jid, jid)
            issn = get_value_in_tag(xml_doc, "ce:issn")
            volume = get_value_in_tag(xml_doc, "vol-first")
            issue = get_value_in_tag(xml_doc, "iss-first")
            year = get_value_in_tag(xml_doc, "start-date")[:4]
            start_date = get_value_in_tag(xml_doc, "start-date")
            if len(start_date) is 8:
                start_date = time.strftime(
                    '%Y-%m-%d', time.strptime(start_date, '%Y%m%d'))
            elif len(start_date) is 6:
                start_date = time.strftime(
                    '%Y-%m', time.strptime(start_date, '%Y%m'))
            for item in xml_doc.getElementsByTagName("ce:include-item"):
                doi = get_value_in_tag(item, "ce:doi")
                first_page = get_value_in_tag(item, "ce:first-page")
                last_page = get_value_in_tag(item, "ce:last-page")
                self._dois[doi] = (journal, issn, volume, issue,
                                   first_page, last_page, year, start_date)

    def _get_doi(self, xml_doc):
        try:
            return get_value_in_tag(xml_doc, "ce:doi")
        except Exception:
            print("Can't find doi", file=sys.stderr)

    def get_title(self, xml_doc):
        try:
            return get_value_in_tag(xml_doc, "ce:title")
        except Exception:
            print("Can't find title", file=sys.stderr)

    def get_abstract(self, xml_doc):
        try:
            abstract_sec = xml_doc.getElementsByTagName("ce:abstract-sec")[0]
            return get_value_in_tag(abstract_sec, "ce:simple-para")
        except Exception:
            print("Can't find abstract", file=sys.stderr)

    def get_keywords(self, xml_doc):
        if self.CONSYN:
            try:
                head = xml_doc.getElementsByTagName("ja:head")[0]
                keywords = head.getElementsByTagName("ce:keyword")
                return [get_value_in_tag(keyword, "ce:text")
                        for keyword in keywords]
            except Exception:
                print("Can't find keywords", file=sys.stderr)
        else:
            try:
                keywords = xml_doc.getElementsByTagName("ce:keyword")
                return [get_value_in_tag(keyword, "ce:text")
                        for keyword in keywords]
            except Exception:
                print("Can't find keywords", file=sys.stderr)

    def get_copyright(self, xml_doc):
        try:
            return get_value_in_tag(xml_doc, "ce:copyright")
        except Exception:
            print("Can't find copyright", file=sys.stderr)

    def get_ref_link(self, xml_doc, name):
        links = xml_doc.getElementsByTagName('ce:inter-ref')
        ret = None
        for link in links:
            if name in link.getAttribute("xlink:href").encode('utf-8'):
                ret = xml_to_text(link).strip()
        return ret

    def get_authors(self, xml_doc):
        authors = []
        for author in xml_doc.getElementsByTagName("ce:author"):
            tmp = {}
            surname = get_value_in_tag(author, "ce:surname")
            if surname:
                tmp["surname"] = surname
            given_name = get_value_in_tag(author, "ce:given-name")
            if given_name:
                tmp["given_name"] = given_name
            initials = get_value_in_tag(author, "ce:initials")
            if initials:
                tmp["initials"] = initials
            orcid = author.getAttribute('orcid').encode('utf-8')
            if orcid:
                tmp["orcid"] = orcid
            emails = author.getElementsByTagName("ce:e-address")
            for email in emails:
                if email.getAttribute("type").encode('utf-8') in ('email', ''):
                    tmp["email"] = xml_to_text(email)
                    break
            cross_refs = author.getElementsByTagName("ce:cross-ref")
            if cross_refs:
                tmp["cross_ref"] = []
                for cross_ref in cross_refs:
                    tmp["cross_ref"].append(
                        cross_ref.getAttribute("refid").encode('utf-8'))
            authors.append(tmp)
        affiliations = {}
        for affiliation in xml_doc.getElementsByTagName("ce:affiliation"):
            aff_id = affiliation.getAttribute("id").encode('utf-8')
            text = re.sub(
                r'^(\d+\ ?)', "", get_value_in_tag(affiliation, "ce:textfn"))
            affiliations[aff_id] = text
        implicit_affilations = True
        for author in authors:
            matching_ref = [ref for ref in author.get(
                "cross_ref", []) if ref in affiliations]
            if matching_ref:
                implicit_affilations = False
                author["affiliation"] = []
                for i in xrange(0, len(matching_ref)):
                    author["affiliation"].append(affiliations[matching_ref[i]])
        if implicit_affilations and len(affiliations) > 1:
            message = "Implicit affiliations are used, "
            message += "but there's more than one affiliation: " + affiliations
            print(message, file=sys.stderr)
        if implicit_affilations and len(affiliations) >= 1:
            for author in authors:
                author["affiliation"] = []
                for aff in affiliations.values():
                    author["affiliation"].append(aff)
        return authors

    def get_publication_information(self, xml_doc):
        if self.CONSYN:
            publication = get_value_in_tag(xml_doc, "prism:publicationName")
            doi = get_value_in_tag(xml_doc, "prism:doi")
            issn = get_value_in_tag(xml_doc, "prism:issn")
            issue = get_value_in_tag(xml_doc, "prism:number")
            first_page = get_value_in_tag(xml_doc, "prism:startingPage")
            last_page = get_value_in_tag(xml_doc, "prism:endingPage")
            journal = publication.split(",")[0]
            journal, volume = fix_journal_name(journal, self.journal_mappings)
            try:
                vol = publication.split(",")[1].strip()
                if vol.startswith("Section"):
                    vol = vol[7:].strip()
                if vol and not volume:
                    volume = vol
            except IndexError:
                pass
            vol = get_value_in_tag(xml_doc, "prism:volume")
            if vol is "":
                # if volume is not present try to harvest it
                try:
                    session = requests.session()
                    r = session.get("http://dx.doi.org/" + doi)
                    parsed_html = BeautifulSoup(r.text)
                    info = parsed_html.body.find(
                        'p', attrs={'class': 'volIssue'}).text.split()
                    for s in info:
                        if unicode(s).find(u'\xe2') > 0:
                            first_page = s.rsplit(u'\xe2')[0]
                            last_page = s.rsplit(u'\x93')[1]
                    if info[1].lower() != 'online':
                        vol = info[1][:-1]
                except:
                    pass
            if vol:
                volume += vol
            year = xml_doc.getElementsByTagName(
                'ce:copyright')[0].getAttribute("year")
            year = year.encode('utf-8')
            start_date = get_value_in_tag(xml_doc, "prism:coverDate")
            if len(xml_doc.getElementsByTagName('ce:date-accepted')) > 0:
                full_date = xml_doc.getElementsByTagName('ce:date-accepted')[0]
                y = full_date.getAttribute('year').encode('utf-8')
                m = full_date.getAttribute('month').encode('utf-8').zfill(2)
                d = full_date.getAttribute('day').encode('utf-8').zfill(2)
                start_date = "%s-%s-%s" % (y, m, d)
            elif len(start_date) is 8:
                start_date = time.strftime(
                    '%Y-%m-%d', time.strptime(start_date, '%Y%m%d'))
            elif len(start_date) is 6:
                start_date = time.strftime(
                    '%Y-%m', time.strptime(start_date, '%Y%m'))
            doi = get_value_in_tag(xml_doc, "ce:doi")
            return (journal, issn, volume, issue, first_page,
                    last_page, year, start_date, doi)
        else:
            doi = self._get_doi(xml_doc)
            try:
                return self._dois[doi] + (doi, )
            except KeyError:
                return ('', '', '', '', '', '', '', '', doi)

    def get_references(self, xml_doc):
        for ref in xml_doc.getElementsByTagName("ce:bib-reference"):
            label = get_value_in_tag(ref, "ce:label")
            authors = []
            for author in ref.getElementsByTagName("sb:author"):
                given_name = get_value_in_tag(author, "ce:given-name")
                surname = get_value_in_tag(author, "ce:surname")
                if given_name:
                    name = "%s, %s" % (surname, given_name)
                else:
                    name = surname
                authors.append(name)
            doi = get_value_in_tag(ref, "ce:doi")
            issue = get_value_in_tag(ref, "sb:issue")
            page = get_value_in_tag(ref, "sb:first-page")
            title = get_value_in_tag(ref, "sb:maintitle")
            volume = get_value_in_tag(ref, "sb:volume-nr")
            tmp_issues = ref.getElementsByTagName('sb:issue')
            if tmp_issues:
                year = get_value_in_tag(tmp_issues[0], "sb:date")[:4]
            else:
                year = ''
            textref = ref.getElementsByTagName("ce:textref")
            if textref:
                textref = xml_to_text(textref[0])
            ext_link = format_arxiv_id(self.get_ref_link(ref, 'arxiv'))
            if self.CONSYN:
                if ext_link and ext_link.lower().startswith('arxiv'):
                    # check if the identifier contains
                    # digits seperated by dot
                    regex = r'\d*\.\d*'
                    if not re.search(regex, ext_link):
                        ext_link = ext_link[6:]
                comment = get_value_in_tag(ref, "sb:comment")
                links = []
                for link in ref.getElementsByTagName("ce:inter-ref"):
                    if link.firstChild:
                        links.append(link.firstChild.data.encode('utf-8'))
                title = ""
                try:
                    container = ref.getElementsByTagName("sb:contribution")[0]
                    title = container.getElementsByTagName("sb:maintitle")[0]
                    title = xml_to_text(title)
                except IndexError:
                    title = ''
                except TypeError:
                    title = ''
                isjournal = ref.getElementsByTagName("sb:issue")
                journal = ""
                if isjournal:
                    container = ref.getElementsByTagName("sb:issue")[0]
                    journal = get_value_in_tag(container, "sb:maintitle")
                edited_book = ref.getElementsByTagName("sb:edited-book")
                editors = []
                book_title = ""
                publisher = ""
                if edited_book:
                    # treat as a journal
                    if ref.getElementsByTagName("sb:book-series"):
                        container = ref.getElementsByTagName(
                            "sb:book-series")[0]
                        journal = get_value_in_tag(container, "sb:maintitle")
                        year = get_value_in_tag(ref, "sb:date")
                        isjournal = True
                    # conference
                    elif ref.getElementsByTagName("sb:conference"):
                        container = ref.getElementsByTagName(
                            "sb:edited-book")[0]
                        maintitle = get_value_in_tag(container, "sb:maintitle")
                        conference = get_value_in_tag(
                            container, "sb:conference")
                        date = get_value_in_tag(container, "sb:date")
                        # use this variable in order to get in the 'm' field
                        publisher = maintitle + ", " + conference + ", " + date
                    else:
                        container = ref.getElementsByTagName(
                            "sb:edited-book")[0]
                        if ref.getElementsByTagName("sb:editors"):
                            for editor in ref.getElementsByTagName("sb:editor"):
                                surname = get_value_in_tag(
                                    editor, "ce:surname")
                                firstname = get_value_in_tag(
                                    editor, "ce:given-name")
                                editors.append("%s,%s" % (surname, firstname))
                        if title:
                            book_title = get_value_in_tag(
                                container, "sb:maintitle")
                        else:
                            title = get_value_in_tag(container, "sb:maintitle")
                        year = get_value_in_tag(container, "sb:date")
                        if ref.getElementsByTagName("sb:publisher"):
                            container = ref.getElementsByTagName(
                                "sb:publisher")[0]
                            location = get_value_in_tag(
                                container, "sb:location")
                            publisher = get_value_in_tag(container, "sb:name")
                            if location:
                                publisher = location + ": " + publisher
                if ref.getElementsByTagName("sb:book"):
                    if ref.getElementsByTagName("sb:book-series"):
                        book_series = ref.getElementsByTagName(
                            "sb:book-series")[0]
                        title += ", " + \
                            get_value_in_tag(book_series, "sb:maintitle")
                        title += ", " + \
                            get_value_in_tag(book_series, "sb:volume-nr")
                    publisher = get_value_in_tag(ref, "sb:publisher")
                if not year:
                    year = get_value_in_tag(ref, "sb:date")
                yield (label, authors, doi, issue, page, title, volume,
                       year, textref, ext_link, isjournal, comment, journal,
                       publisher, editors, book_title)
            else:
                yield (label, authors, doi, issue, page, title, volume,
                       year, textref, ext_link)

    def get_article_journal(self, xml_doc):
        if self.CONSYN:
            return CFG_ELSEVIER_JID_MAP[get_value_in_tag(xml_doc, "ja:jid")]
        else:
            return CFG_ELSEVIER_JID_MAP[get_value_in_tag(xml_doc, "jid")]

    def get_article(self, path):
        if path.endswith('.xml'):
            data_file = path
        else:
            data_file = open(join(path, "resolved_main.xml"))
        return parse(data_file)

    def get_elsevier_version(self, name):
        try:
            ret = name[0:5]
            if ret[4] is "A":
                ret = ret + "B"
            return ret
        except Exception:
            raise

    def get_pdfa_record(self, path=None):
        from invenio.search_engine import search_pattern
        xml_doc = self.get_article(path)
        rec = {}
        dummy, dummy, dummy, dummy, dummy, dummy, dummy,\
            dummy, doi = self.get_publication_information(xml_doc)
        recid = search_pattern(p='0247_a:"%s" AND NOT 980:"DELETED"' % (doi,))
        if recid:
            record_add_field(rec, '001', controlfield_value=recid[0])
        else:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
            message = 'Adding PDF/A. No paper with this DOI: %s. Trying to add it anyway.' % (
                doi,)
            self.logger.error(message)
            register_exception(alert_admin=True, prefix=message)
        try:
            if exists(join(path, 'main_a-2b.pdf')):
                record_add_field(
                    rec, 'FFT', subfields=[('a', join(path, 'main_a-2b.pdf')),
                                ('n', 'main'),
                        ('f', '.pdf;pdfa')])
                self.logger.debug('Adding PDF/A to record: %s' % (doi,))
            elif exists(join(path, 'main.pdf')):
                record_add_field(
                    rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
                message = 'No PDF/A in VTEX package for record: ' + doi
                self.logger.debug(message)
            else:
                message = "Record %s doesn't contain PDF file." % (doi,)
                raise MissingFFTError(message)
        except MissingFFTError:
            message = "Elsevier paper: %s is missing PDF." % (doi,)
            register_exception(alert_admin=True, prefix=message)
            self.logger.warning(message)
        return record_xml_output(rec)

    def get_record(self, path=None, no_pdf=False):
        xml_doc = self.get_article(path)
        rec = {}
        title = self.get_title(xml_doc)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        journal, dummy, volume, issue, first_page,\
            last_page, year, start_date, doi = self.get_publication_information(
                xml_doc)
        if not journal:
            journal = self.get_article_journal(xml_doc)
        if start_date:
            record_add_field(rec, '260', subfields=[('c', start_date)])
        else:
            record_add_field(
                rec, '260', subfields=[('c', time.strftime('%Y-%m-%d'))])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        self.logger.info("Creating record: %s %s" % (path, doi))
        authors = self.get_authors(xml_doc)
        first_author = True
        for author in authors:
            author_name = (author['surname'], author.get(
                'given_name') or author.get('initials'))
            subfields = [('a', '%s, %s' % author_name)]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('v', aff))
            if author.get('email'):
                subfields.append(('m', author['email']))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        abstract = self.get_abstract(xml_doc)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract),
                                                    ('9', 'Elsevier')])
        copyrightt = self.get_copyright(xml_doc)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyrightt)])
        keywords = self.get_keywords(xml_doc)
        if self.CONSYN:
            if keywords:
                for keyword in keywords:
                    record_add_field(
                        rec, '653', ind1='1', subfields=[('a', keyword),
                                    ('9', 'author')])
            if first_page and last_page:
                record_add_field(rec, '773', subfields=[('p', journal),
                                                        ('v', volume),
                                                        ('n', issue),
                                                        ('c', '%s-%s' % (
                                                            first_page, last_page)),
                                                        ('y', year)])
            else:
                record_add_field(rec, '773', subfields=[('p', journal),
                                                        ('v', volume),
                                                        ('n', issue),
                                                        ('y', year)])
        else:
            licence = 'http://creativecommons.org/licenses/by/3.0/'
            record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'),
                                                    ('u', licence)])
            if keywords:
                for keyword in keywords:
                    record_add_field(
                        rec, '653', ind1='1', subfields=[('a', keyword),
                                    ('9', 'author')])
            record_add_field(rec, '773', subfields=[('p', journal),
                                                    ('v', volume),
                                                    ('n', issue),
                                                    ('c', '%s-%s' % (
                                                        first_page, last_page)),
                                                    ('y', year)])
        self._add_references(xml_doc, rec)

        if not no_pdf:
            from invenio.search_engine import search_pattern
            query = '0247_a:"%s" AND NOT 980:DELETED"' % (doi,)
            prev_version = search_pattern(p=query)
            from invenio.bibdocfile import BibRecDocs
            old_pdf = False

            if prev_version:
                prev_rec = BibRecDocs(prev_version[0])
                try:
                    pdf_path = prev_rec.get_bibdoc('main')
                    pdf_path = pdf_path.get_file(
                        ".pdf;pdfa", exact_docformat=True)
                    pdf_path = pdf_path.fullpath
                    old_pdf = True
                    record_add_field(rec, 'FFT', subfields=[('a', pdf_path),
                                                            ('n', 'main'),
                                                            ('f', '.pdf;pdfa')])
                    message = 'Leaving previously delivered PDF/A for: ' + doi
                    self.logger.info(message)
                except:
                    pass
            try:
                if exists(join(path, 'main_a-2b.pdf')):
                    path = join(path, 'main_a-2b.pdf')
                    record_add_field(rec, 'FFT', subfields=[('a', path),
                                                            ('n', 'main'),
                                                            ('f', '.pdf;pdfa')])
                    self.logger.debug('Adding PDF/A to record: %s' % (doi,))
                elif exists(join(path, 'main.pdf')):
                    path = join(path, 'main.pdf')
                    record_add_field(rec, 'FFT', subfields=[('a', path)])
                else:
                    if not old_pdf:
                        message = "Record " + doi
                        message += " doesn't contain PDF file."
                        self.logger.warning(message)
                        raise MissingFFTError(message)
            except MissingFFTError:
                message = "Elsevier paper: %s is missing PDF." % (doi,)
                register_exception(alert_admin=True, prefix=message)
        if self.CONSYN:
            record_add_field(rec, 'FFT', subfields=[('a', path),
                                                    ('t', 'Elsevier'),
                                                    ('o', 'HIDDEN')])
            record_add_field(rec, '980', subfields=[('a', 'HEP')])
            record_add_field(rec, '980', subfields=[('a', 'Citeable')])
            record_add_field(rec, '980', subfields=[('a', 'Published')])
        else:
            version = self.get_elsevier_version(find_package_name(path))
            record_add_field(rec, '583', subfields=[('l', version)])
            path = join(path, 'main.xml')
            record_add_field(rec, 'FFT', subfields=[('a', path)])
            record_add_field(rec, '980', subfields=[('a', 'SCOAP3'),
                                                    ('b', 'Elsevier')])
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

    def bibupload_it(self):
        print(self.found_articles)
        if self.found_articles:
            if [x for x in self.found_articles if "vtex" not in x]:
                self.logger.debug("Preparing bibupload.")
                fd, name = mkstemp(suffix='.xml',
                                   prefix='bibupload_scoap3_',
                                   dir=CFG_TMPSHAREDDIR)
                out = fdopen(fd, 'w')
                print("<collection>", file=out)
                for i, path in enumerate(self.found_articles):
                    if "vtex" not in path:
                        print(self.get_record(path),
                              file=out)
                        print(path, i + 1, "out of", len(self.found_articles))
                print("</collection>", file=out)
                out.close()
                task_low_level_submission(
                    "bibupload", "admin", "-N", "Elsevier", "-i", "-r", name)
            if [x for x in self.found_articles if "vtex" in x]:
            # for VTEX files with PDF/A
                self.logger.debug("Preparing bibupload for PDF/As.")
                fd_vtex, name_vtex = mkstemp(
                    suffix='.xml', prefix='bibupload_scoap3_',
                    dir=CFG_TMPSHAREDDIR)
                out = fdopen(fd_vtex, 'w')
                print("<collection>", file=out)
                # enumerate remember progres of prevoius one
                for i, path in enumerate(self.found_articles):
                    if "vtex" in path:
                        print(self.get_pdfa_record(path), file=out)
                        print(path, i + 1, "out of", len(self.found_articles))
                print("</collection>", file=out)
                out.close()
                task_low_level_submission("bibupload", "admin", "-N",
                                          "Elsevier:VTEX", "-a", name_vtex)


def main():
    try:
        if len(sys.argv) > 2:
            print("Unrecognized number of parameters.")
            print("Try giving a package name or run with --run-localy.")
            sys.exit(1)
        if len(sys.argv) < 2:
            els = ElsevierPackage()
        elif len(sys.argv) == 2:
            if sys.argv[1] == "--run-localy":
                els = ElsevierPackage(run_localy=True)
            else:
                path_or_package = sys.argv[1]
                if path_or_package.endswith((".tar", ".zip")):
                    els = ElsevierPackage(package_name=path_or_package)
                else:
                    els = ElsevierPackage(path=path_or_package)
        els.bibupload_it()
    except Exception as err:
        register_exception()
        print("ERROR: Exception captured: %s" % err)
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
