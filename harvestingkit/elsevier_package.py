# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2013, 2014, 2015, 2017 CERN.
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
import time
import requests
import xml.dom.minidom
import datetime

from bs4 import BeautifulSoup
from os import (listdir,
                rename,
                fdopen)
from os.path import (join,
                     exists,
                     walk)
from tempfile import (mkdtemp,
                      mkstemp)
from zipfile import ZipFile
from xml.dom.minidom import parse


try:
    from invenio.errorlib import register_exception
except ImportError:
    register_exception = lambda a, b: True

try:
    from invenio.config import CFG_TMPSHAREDDIR, CFG_LOGDIR
except ImportError:
    from distutils.sysconfig import get_python_lib
    CFG_TMPSHAREDDIR = join(get_python_lib(),
                            "harvestingkit",
                            "tmp")
    CFG_LOGDIR = join(get_python_lib(),
                      "harvestingkit",
                      "log")

from harvestingkit.utils import (create_logger, make_user_agent, run_shell_command)

from harvestingkit.scoap3utils import (
    MissingFFTError,
    extract_package as scoap3utils_extract_package
)
from harvestingkit.contrast_out_utils import find_package_name
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.config import CFG_DTDS_PATH as CFG_SCOAP3DTDS_PATH
from harvestingkit.utils import (fix_journal_name,
                                 format_arxiv_id,
                                 add_nations_field,
                                 fix_dashes)

from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
    record_xml_output,
)

CFG_ELSEVIER_ART501_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art501.zip')
CFG_ELSEVIER_ART510_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art510.zip')
CFG_ELSEVIER_ART520_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art520.zip')
CFG_ELSEVIER_ART540_PATH = join(CFG_SCOAP3DTDS_PATH, 'ja5_art540.zip')
CFG_ELSEVIER_SI510_PATH = join(CFG_SCOAP3DTDS_PATH, 'si510.zip')
CFG_ELSEVIER_SI520_PATH = join(CFG_SCOAP3DTDS_PATH, 'si520.zip')
CFG_ELSEVIER_SI540_PATH = join(CFG_SCOAP3DTDS_PATH, 'si540.zip')
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

    :param package_name: the path to a tar.gz file to expand and parse
    :type package_name: string
    :param path: the actual path of an already expanded package.
    :type package_name: string
    :param CONSYN: flag to determine which conversion should be used.
    :type package_name: bool
    :param journal_mappings: dictionary used to convert journal names
                       key: the name in the xml source files
                       value: the desired name.
    :type package_name: dict

    :note: either C{package_name} or C{path} don't have to be passed to the
    constructor, in this case the Elsevier server will be harvested.

    """
    def __init__(self, package_name=None, path=None,
                 run_locally=False, CONSYN=False,
                 journal_mappings={},
                 extract_nations=False,
                 no_harvest=False):
        self.CONSYN = CONSYN
        self.doi_package_name_mapping = []
        try:
            self.logger = create_logger(
                "Elsevier",
                filename=join(CFG_LOGDIR, 'scoap3_harvesting.log')
            )
        except IOError:  # Could not access log file
                         # Use std.out for logging
            self.logger = self
            self.info = print
            self.warning = print
            self.error = print
            self.debug = print
        if self.CONSYN:
            self.journal_mappings = journal_mappings
        else:
            if not no_harvest:
                self.package_name = package_name
                self.path = path
                self.found_articles = []
                self._found_issues = []
                if run_locally:
                    from harvestingkit.contrast_out import ContrastOutConnector
                    self.conn = ContrastOutConnector(self.logger)
                    self.conn.run(run_locally)
                else:
                    if not path and package_name:
                        self.logger.info("Got package: %s" % (package_name,))
                        self._extract_package()
                    elif not path and not package_name:
                        from harvestingkit.contrast_out import ContrastOutConnector
                        self.conn = ContrastOutConnector(self.logger)
                        self.conn.run()
                self._crawl_elsevier_and_find_main_xml()
                self._crawl_elsevier_and_find_issue_xml()
                self._build_doi_mapping()
        self.extract_nations = extract_nations

    def _extract_package(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path = mkdtemp(prefix="scoap3_package_", dir=CFG_TMPSHAREDDIR)
        self.logger.debug("Extracting package: %s" % (self.package_name,))
        scoap3utils_extract_package(self.package_name, self.path, self.logger)

    def _crawl_elsevier_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in a given directory.
        """
        self.found_articles = []
        if not self.path and not self.package_name:
            for doc in self.conn.found_articles:
                dirname = doc['xml'].rstrip('/main.xml')
                try:
                    self._normalize_article_dir_with_dtd(dirname)
                    self.found_articles.append(dirname)
                except Exception as err:
                    register_exception()
                    print("ERROR: can't normalize %s: %s" % (dirname, err))
        else:
            def visit(dummy, dirname, names):
                if "main.xml" in names and "main.pdf" in names:
                    try:
                        self._normalize_article_dir_with_dtd(dirname)
                        self.found_articles.append(dirname)
                    except Exception as err:
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


    def _extract_correct_dtd_package(self, si_name, path):
        try:
            ZipFile(eval("CFG_ELSEVIER_%s_PATH" % si_name.upper())).extractall(path)
        except Exception as e:
                raise e
        for filename in listdir(join(path, si_name)):
            rename(join(path, si_name, filename), join(path, filename))


    def _normalize_issue_dir_with_dtd(self, path):
        """
        issue.xml from Elsevier assume the existence of a local DTD.
        This procedure install the DTDs next to the issue.xml file
        and normalize it using xmllint in order to resolve all namespaces
        and references.
        """
        if exists(join(path, 'resolved_issue.xml')):
            return
        issue_xml_content = open(join(path, 'issue.xml')).read()
        sis = ['si510.dtd', 'si520.dtd', 'si540.dtd']
        tmp_extracted = 0
        for si in sis:
            if si in issue_xml_content:
                self._extract_correct_dtd_package(si.split('.')[0], path)
                tmp_extracted = 1

        if not tmp_extracted:
            message = "It looks like the path " + path
            message += " does not contain an si510, si520 or si540 in issue.xml file"
            self.logger.error(message)
            raise ValueError(message)
        command = ["xmllint", "--format", "--loaddtd",
                   join(path, 'issue.xml'),
                   "--output", join(path, 'resolved_issue.xml')]
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
        main_xml_content = open(join(path, 'main.xml')).read()
        arts = ['art501.dtd','art510.dtd','art520.dtd','art540.dtd']
        tmp_extracted = 0
        for art in arts:
            if art in main_xml_content:
                self._extract_correct_dtd_package(art.split('.')[0], path)
                tmp_extracted = 1

        if not tmp_extracted:
            message = "It looks like the path " + path
            message += "does not contain an art501, art510, art520 or art540 in main.xml file"
            self.logger.error(message)
            raise ValueError(message)
        command = ["xmllint", "--format", "--loaddtd",
                   join(path, 'main.xml'),
                   "--output", join(path, 'resolved_main.xml')]
        dummy, dummy, cmd_err = run_shell_command(command)
        if cmd_err:
            message = "Error in cleaning %s: %s" % (
                join(path, 'main.xml'), cmd_err)
            self.logger.error(message)
            raise ValueError(message)

    def _add_references(self, xml_doc, rec, refextract_callback=None):
        for label, authors, doi, issue, page, title, volume, year,\
                textref, ext_link, isjournal, comment, journal, publisher,\
                editors, book_title in self.get_references(xml_doc):
            subfields = []
            if textref and not authors:
                textref = textref.replace('\"', '\'')
                if refextract_callback:
                    ref_xml = refextract_callback(textref)
                    dom = xml.dom.minidom.parseString(ref_xml)
                    fields = dom.getElementsByTagName("datafield")[0]
                    fields = fields.getElementsByTagName("subfield")
                    for field in fields:
                        data = field.firstChild.data
                        code = field.getAttribute("code")
                        if code == 'r':
                            data = fix_dashes(data)
                        subfields.append((code, data))
                    if fields:
                        subfields.append(('9', 'refextract'))
                else:
                    subfields.append(('m', textref))
                if label:
                    label = re.sub("[\[\].)]", "", label)
                    subfields.append(('o', label))
                if subfields:
                    record_add_field(rec, '999', ind1='C', ind2='5',
                                     subfields=subfields)
            else:
                if doi:
                    subfields.append(('a', doi))
                for author in authors:
                    subfields.append(('h', author))
                if ext_link:
                    ext_link = fix_dashes(ext_link)
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
                if journal:
                    journal, vol = fix_journal_name(journal,
                                                    self.journal_mappings)
                    volume = vol + volume
                    if volume and page:
                        journal = journal + "," + volume + "," + page
                        subfields.append(('s', journal))
                    elif volume:
                        journal = journal + "," + volume
                        subfields.append(('s', journal))
                    else:
                        subfields.append(('s', journal))
                if textref:
                    subfields.append(('m', textref))
                if subfields:
                    record_add_field(rec, '999', ind1='C', ind2='5',
                                     subfields=subfields)

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

    def get_doctype(self, xml_doc):
        doctype = xml_doc.getElementsByTagName('cja:converted-article')
        if not doctype:
            doctype = xml_doc.getElementsByTagName('ja:article')
        if not doctype:
            doctype = xml_doc.getElementsByTagName('ja:simple-article')
        try:
            doctype = doctype[0].getAttribute('docsubtype')
        except IndexError:
            print('Cannot find doctype!!!')
            return ''
        return doctype

    def get_abstract(self, xml_doc):
        try:
            abstract_sec = xml_doc.getElementsByTagName("ce:abstract-sec")[0]
            return get_value_in_tag(abstract_sec, "ce:simple-para")
        except Exception:
            print("Can't find abstract", file=sys.stderr)

    def get_keywords(self, xml_doc):
        head = xml_doc.getElementsByTagName("ja:head")
        if not head: 
            head = xml_doc.getElementsByTagName("cja:head")
        if not head:
            keywords = xml_doc.getElementsByTagName("ce:keyword")
        else:
            keywords = head[0].getElementsByTagName("ce:keyword")
        return [get_value_in_tag(keyword, "ce:text") 
                for keyword in keywords 
                if get_value_in_tag(keyword, "ce:text")]

    def get_copyright(self, xml_doc):
        try:
            copyright = get_value_in_tag(xml_doc, "ce:copyright")
            if not copyright:
                copyright = get_value_in_tag(xml_doc, "prism:copyright")
            return copyright
        except Exception:
            print("Can't find copyright", file=sys.stderr)

    def get_ref_link(self, xml_doc, name):
        links = xml_doc.getElementsByTagName('ce:inter-ref')
        ret = None
        for link in links:
            if name in link.getAttribute("xlink:href").encode('utf-8'):
                ret = xml_to_text(link).strip()
        return ret

    def _author_dic_from_xml(self, author):
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

        return tmp

    def _affiliation_from_sa_field(self, affiliation):
        sa_affiliation = affiliation.getElementsByTagName('sa:affiliation')
        if sa_affiliation:
            return xml_to_text(sa_affiliation[0], ', ')
        else:
            affiliation = re.sub(r'^(\d+\ ?)',"",get_value_in_tag(affiliation, "ce:textfn"))
            if affiliation:
                return affiliation
            else:
                raise IndexError

    def _find_affiliations(self, xml_doc, doi):
        try:
            return dict((aff.getAttribute("id").encode('utf-8'),
                        self._affiliation_from_sa_field(aff))
                        for aff in xml_doc.getElementsByTagName("ce:affiliation"))
        except IndexError:
            message = "Elsevier paper: {0} is missing sa:affiliation."
            register_exception(alert_admin=True, prefix=message.format(doi))

    def _add_affiliations_to_author(self, author, affs):
        if affs:
            try:
                author['affiliation'].extend(affs)
            except KeyError:
                author['affiliation'] = affs

        return len(affs)

    def _add_referenced_affiliation(self, author, affiliations):
        affs = [affiliations[ref] for ref in author.get("cross_ref", [])
                if ref in affiliations]

        return self._add_affiliations_to_author(author, affs)

    def _add_group_affiliation(self, author, xml_author):
        affs = [get_value_in_tag(aff, "ce:textfn") for aff in
                xml_author.parentNode.getElementsByTagName('ce:affiliation')]

        return self._add_affiliations_to_author(author, affs)

    def _get_direct_children(self, element, tagname):
        affs = []
        for child in element.childNodes:
            try:
                if child.tagName == tagname:
                    affs.append(child)
            except AttributeError:
                pass
        return affs

    def _add_global_affiliation(self, author, xml_author):
        affs = []
        # get author_group of author, already done in group_affiliation
        # this goes higher in the hierarchy
        parent = xml_author.parentNode
        while True:
            try:
                parent = parent.parentNode
                affs.extend([get_value_in_tag(aff, "ce:textfn") for aff
                             in self._get_direct_cildren(parent,
                                                         'ce:affiliation')])
            except AttributeError:
                break

        return self._add_affiliations_to_author(author, affs)

    def _add_affiliations(self, authors, xml_authors, affiliations):
        for xml_author, author in zip(xml_authors, authors):
            if not self._add_referenced_affiliation(author, affiliations):
                self._add_group_affiliation(author, xml_author)
            self._add_global_affiliation(author, xml_author)

    def _add_orcids(self, authors, xml_authors):
        for author, xml_author in zip(authors, xml_authors):
            try:
                orcid = xml_author.getAttribute('orcid')
                if orcid:
                    author['orcid'] = 'ORCID:{0}'.format(orcid)
            except IndexError:
                continue

    def get_authors(self, xml_doc):
            xml_authors = xml_doc.getElementsByTagName("ce:author")
            authors = [self._author_dic_from_xml(author) for author
                       in xml_authors]

            doi = self._get_doi(xml_doc)

            self._add_affiliations(authors, xml_authors,
                                   self._find_affiliations(xml_doc, doi))

            self._add_orcids(authors, xml_authors)

            return authors

    def get_publication_information(self, xml_doc, path='', timeout=60):
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
            if vol is "" and path is not "":
                # if volume is not present try to harvest it
                try:
                    session = requests.session()
                    url = 'http://www.sciencedirect.com/science/article/pii'\
                          + path.split('/')[-1]
                    headers = {'user-agent': make_user_agent()}
                    r = session.get(url, headers=headers, timeout=timeout)
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
            start_date = self.get_publication_date(xml_doc)
            year = start_date.split("-")[0]
            doi = get_value_in_tag(xml_doc, "ce:doi")
            return (journal, issn, volume, issue, first_page,
                    last_page, year, start_date, doi)
        else:
            doi = self._get_doi(xml_doc)
            try:
                return self._dois[doi] + (doi, )
            except KeyError:
                return ('', '', '', '', '', '', '', '', doi)

    def get_publication_date(self, xml_doc):
        """Return the best effort start_date."""
        start_date = get_value_in_tag(xml_doc, "prism:coverDate")
        if not start_date:
            start_date = get_value_in_tag(xml_doc, "prism:coverDisplayDate")
            if not start_date:
                start_date = get_value_in_tag(xml_doc, 'oa:openAccessEffective')
                if start_date:
                    start_date = datetime.datetime.strptime(
                        start_date, "%Y-%m-%dT%H:%M:%SZ"
                    )
                    return start_date.strftime("%Y-%m-%d")
            import dateutil.parser
            try:
                date = dateutil.parser.parse(start_date)
            except ValueError:
                return ''
            # Special case where we ignore the deduced day form dateutil
            # in case it was not given in the first place.
            if len(start_date.split(" ")) == 3:
                return date.strftime("%Y-%m-%d")
            else:
                return date.strftime("%Y-%m")
        else:
            if len(start_date) is 8:
                start_date = time.strftime(
                    '%Y-%m-%d', time.strptime(start_date, '%Y%m%d'))
            elif len(start_date) is 6:
                start_date = time.strftime(
                    '%Y-%m', time.strptime(start_date, '%Y%m'))
            return start_date

    def _get_ref(self, ref, label):
        doi = get_value_in_tag(ref, "ce:doi")
        page = get_value_in_tag(ref, "sb:first-page")
        if not page:
            page = get_value_in_tag(ref, "sb:article-number")
        issue = get_value_in_tag(ref, "sb:issue")
        title = get_value_in_tag(ref, "sb:maintitle")
        volume = get_value_in_tag(ref, "sb:volume-nr")
        tmp_issues = ref.getElementsByTagName('sb:issue')
        if tmp_issues:
            year = get_value_in_tag(tmp_issues[0], "sb:date")
        else:
            year = ''
        textref = ref.getElementsByTagName("ce:textref")
        if textref:
            textref = xml_to_text(textref[0])
        ext_link = format_arxiv_id(self.get_ref_link(ref, 'arxiv'))
        authors = []
        for author in ref.getElementsByTagName("sb:author"):
            given_name = get_value_in_tag(author, "ce:given-name")
            surname = get_value_in_tag(author, "ce:surname")
            if given_name:
                name = "%s, %s" % (surname, given_name)
            else:
                name = surname
            authors.append(name)
        if ext_link and ext_link.lower().startswith('arxiv'):
            # check if the identifier contains
            # digits seperated by dot
            regex = r'\d*\.\d*'
            if not re.search(regex, ext_link):
                ext_link = ext_link[6:]
        comment = get_value_in_tag(ref, "sb:comment")
        links = []
        for link in ref.getElementsByTagName("ce:inter-ref"):
            links.append(xml_to_text(link))
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
            isjournal = True
            if not page:
                page = comment
            container = ref.getElementsByTagName("sb:issue")[0]
            journal = get_value_in_tag(container, "sb:maintitle")
        edited_book = ref.getElementsByTagName("sb:edited-book")
        editors = []
        book_title = ""
        publisher = ""
        if edited_book:
            # treat as a journal
            if ref.getElementsByTagName("sb:book-series"):
                container = ref.getElementsByTagName("sb:book-series")[0]
                journal = get_value_in_tag(container, "sb:maintitle")
                year = get_value_in_tag(ref, "sb:date")
                isjournal = True
            # conference
            elif ref.getElementsByTagName("sb:conference"):
                container = ref.getElementsByTagName("sb:edited-book")[0]
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
                        surname = get_value_in_tag(editor, "ce:surname")
                        firstname = get_value_in_tag(editor, "ce:given-name")
                        editors.append("%s,%s" % (surname, firstname))
                if title:
                    book_title = get_value_in_tag(
                        container, "sb:maintitle")
                else:
                    title = get_value_in_tag(container, "sb:maintitle")
                year = get_value_in_tag(container, "sb:date")
                if ref.getElementsByTagName("sb:publisher"):
                    container = ref.getElementsByTagName("sb:publisher")[0]
                    location = get_value_in_tag(container, "sb:location")
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
        year = re.sub(r'\D', '', year)
        return (label, authors, doi, issue, page, title, volume,
                year, textref, ext_link, isjournal, comment, journal,
                publisher, editors, book_title)

    def get_references(self, xml_doc):
        for ref in xml_doc.getElementsByTagName("ce:bib-reference"):
            label = get_value_in_tag(ref, "ce:label")
            innerrefs = ref.getElementsByTagName("sb:reference")
            if not innerrefs:
                yield self._get_ref(ref, label)
            for inner in innerrefs:
                yield self._get_ref(inner, label)

    def get_article_journal(self, xml_doc):
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
        from invenio.search_engine import perform_request_search
        xml_doc = self.get_article(path)
        rec = create_record()
        dummy, dummy, dummy, dummy, dummy, dummy, dummy,\
            dummy, doi = self.get_publication_information(xml_doc)
        recid = perform_request_search(p='0247_a:"%s" AND NOT 980:"DELETED"' % (doi,))
        if recid:
            record_add_field(rec, '001', controlfield_value=recid[0])
        else:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
            message = ('Adding PDF/A. No paper with this DOI: '
                       '%s. Trying to add it anyway.') % (doi,)
            self.logger.error(message)
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

        ## copy other formats to bibupload file
        if recid:
            from invenio.bibdocfile import BibRecDocs
            record = BibRecDocs(recid[0])
            for bibfile in record.list_latest_files():
                if bibfile.get_format() != '.pdf;pdfa':
                    record_add_field(rec,
                                     'FFT',
                                     subfields=[('a', bibfile.get_full_path()),
                                                ('n', bibfile.get_name()),
                                                ('f', bibfile.get_format())]
                                     )
        return record_xml_output(rec)

    def get_license(self, xml_doc):
        license = ''
        license_url = ''
        for tag in xml_doc.getElementsByTagName('oa:openAccessInformation'):
            license_url = get_value_in_tag(tag, 'oa:userLicense')
        if license_url.startswith('http://creativecommons.org/licenses/by/3.0'):
            license = 'CC-BY-3.0'
        return license, license_url

    def get_record(self, path=None, no_pdf=False,
                   test=False, refextract_callback=None):
        """Convert a record to MARCXML format.

        :param path: path to a record.
        :type path: string
        :param test: flag to determine if it is a test call.
        :type test: bool
        :param refextract_callback: callback to be used to extract
                                    unstructured references. It should
                                    return a marcxml formated string
                                    of the reference.
        :type refextract_callback: callable

        :returns: marcxml formated string.
        """
        xml_doc = self.get_article(path)
        rec = create_record()
        title = self.get_title(xml_doc)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        (journal, dummy, volume, issue, first_page, last_page, year,
         start_date, doi) = self.get_publication_information(xml_doc, path)
        if not journal:
            journal = self.get_article_journal(xml_doc)
        if start_date:
            record_add_field(rec, '260', subfields=[('c', start_date),
                                                    ('t', 'published')])
        else:
            record_add_field(
                rec, '260', subfields=[('c', time.strftime('%Y-%m-%d'))])
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi),
                                                              ('2', 'DOI')])
        license, license_url = self.get_license(xml_doc)
        if license and license_url:
            record_add_field(rec, '540', subfields=[('a', license),
                                                    ('u', license_url)])
        elif license_url:
            record_add_field(rec, '540', subfields=[('u', license_url)])
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

                if self.extract_nations:
                    add_nations_field(subfields)

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
        record_copyright = self.get_copyright(xml_doc)
        if record_copyright:
            record_add_field(rec, '542', subfields=[('f', record_copyright)])
        keywords = self.get_keywords(xml_doc)
        if self.CONSYN:
            for tag in xml_doc.getElementsByTagName('ce:collaboration'):
                collaboration = get_value_in_tag(tag, 'ce:text')
                if collaboration:
                    record_add_field(rec, '710',
                                     subfields=[('g', collaboration)])

            # We add subjects also as author keywords
            subjects = xml_doc.getElementsByTagName('dct:subject')
            for subject in subjects:
                for listitem in subject.getElementsByTagName('rdf:li'):
                    keyword = xml_to_text(listitem)
                    if keyword not in keywords:
                        keywords.append(keyword)
            for keyword in keywords:
                record_add_field(rec, '653', ind1='1',
                                 subfields=[('a', keyword),
                                            ('9', 'author')])
            journal, dummy = fix_journal_name(journal.strip(),
                                              self.journal_mappings)
            subfields = []
            doctype = self.get_doctype(xml_doc)
            try:
                page_count = int(last_page) - int(first_page) + 1
                record_add_field(rec, '300',
                                 subfields=[('a', str(page_count))])
            except ValueError:  # do nothing
                pass
            if doctype == 'err':
                subfields.append(('m', 'Erratum'))
            elif doctype == 'add':
                subfields.append(('m', 'Addendum'))
            elif doctype == 'pub':
                subfields.append(('m', 'Publisher Note'))
            elif doctype == 'rev':
                record_add_field(rec, '980', subfields=[('a', 'Review')])
            if journal:
                subfields.append(('p', journal))
            if first_page and last_page:
                subfields.append(('c', '%s-%s' %
                                       (first_page, last_page)))
            elif first_page:
                subfields.append(('c', first_page))
            if volume:
                subfields.append(('v', volume))
            if year:
                subfields.append(('y', year))
            record_add_field(rec, '773', subfields=subfields)
            if not test:
                if license:
                    url = 'http://www.sciencedirect.com/science/article/pii/'\
                          + path.split('/')[-1][:-4]
                    record_add_field(rec, '856', ind1='4',
                                     subfields=[('u', url),
                                                ('y', 'Elsevier server')])
                    record_add_field(rec, 'FFT', subfields=[('a', path),
                                                            ('t', 'INSPIRE-PUBLIC'),
                                                            ('d', 'Fulltext')])
                else:
                    record_add_field(rec, 'FFT', subfields=[('a', path),
                                                            ('t', 'Elsevier'),
                                                            ('o', 'HIDDEN')])
            record_add_field(rec, '980', subfields=[('a', 'HEP')])
            record_add_field(rec, '980', subfields=[('a', 'Citeable')])
            record_add_field(rec, '980', subfields=[('a', 'Published')])
            self._add_references(xml_doc, rec, refextract_callback)
        else:
            licence = 'http://creativecommons.org/licenses/by/3.0/'
            record_add_field(rec,
                             '540',
                             subfields=[('a', 'CC-BY-3.0'), ('u', licence)])
            if keywords:
                for keyword in keywords:
                    record_add_field(
                        rec, '653', ind1='1', subfields=[('a', keyword),
                                    ('9', 'author')])

            pages = ''
            if first_page and last_page:
                pages = '{0}-{1}'.format(first_page, last_page)
            elif first_page:
                pages = first_page

            subfields = filter(lambda x: x[1] and x[1] != '-', [('p', journal),
                                                                ('v', volume),
                                                                ('n', issue),
                                                                ('c', pages),
                                                                ('y', year)])

            record_add_field(rec, '773', subfields=subfields)
            if not no_pdf:
                from invenio.search_engine import perform_request_search
                query = '0247_a:"%s" AND NOT 980:DELETED"' % (doi,)
                prev_version = perform_request_search(p=query)

                old_pdf = False

                if prev_version:
                    from invenio.bibdocfile import BibRecDocs
                    prev_rec = BibRecDocs(prev_version[0])
                    try:
                        pdf_path = prev_rec.get_bibdoc('main')
                        pdf_path = pdf_path.get_file(
                            ".pdf;pdfa", exact_docformat=True)
                        pdf_path = pdf_path.fullpath
                        old_pdf = True
                        record_add_field(rec, 'FFT',
                                         subfields=[('a', pdf_path),
                                                    ('n', 'main'),
                                                    ('f', '.pdf;pdfa')])
                        message = ('Leaving previously delivered PDF/A for: '
                                   + doi)
                        self.logger.info(message)
                    except:
                        pass
                try:
                    if exists(join(path, 'main_a-2b.pdf')):
                        pdf_path = join(path, 'main_a-2b.pdf')
                        record_add_field(rec, 'FFT',
                                         subfields=[('a', pdf_path),
                                                    ('n', 'main'),
                                                    ('f', '.pdf;pdfa')])
                        self.logger.debug('Adding PDF/A to record: %s'
                                          % (doi,))
                    elif exists(join(path, 'main.pdf')):
                        pdf_path = join(path, 'main.pdf')
                        record_add_field(rec, 'FFT', subfields=[('a', pdf_path)])
                    else:
                        if not old_pdf:
                            message = "Record " + doi
                            message += " doesn't contain PDF file."
                            self.logger.warning(message)
                            raise MissingFFTError(message)
                except MissingFFTError:
                    message = "Elsevier paper: %s is missing PDF." % (doi,)
                    register_exception(alert_admin=True, prefix=message)
                version = self.get_elsevier_version(find_package_name(path))
                record_add_field(rec, '583', subfields=[('l', version)])
                xml_path = join(path, 'main.xml')
                record_add_field(rec, 'FFT', subfields=[('a', xml_path)])
                record_add_field(rec, '980', subfields=[('a', 'SCOAP3'),
                                                        ('b', 'Elsevier')])
        try:
            return record_xml_output(rec)
        except UnicodeDecodeError:
            message = "Found a bad char in the file for the article " + doi
            sys.stderr.write(message)
            return ""

    def bibupload_it(self):
        from invenio.bibtask import task_low_level_submission
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
                        xml_doc = self.get_article(path)
                        doi = self._get_doi(xml_doc)
                        package_name = filter(lambda x: 'cern' in x.lower() or 'vtex' in x.lower(), path.split('/'))
                        if package_name:
                            self.doi_package_name_mapping.append((package_name[0], doi))
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
                # enumerate remember progress of previous one
                for i, path in enumerate(self.found_articles):
                    if "vtex" in path:
                        print(self.get_pdfa_record(path), file=out)
                        print(path, i + 1, "out of", len(self.found_articles))
                print("</collection>", file=out)
                out.close()
                task_low_level_submission("bibupload", "admin", "-N",
                                          "Elsevier:VTEX", "-c", name_vtex)
