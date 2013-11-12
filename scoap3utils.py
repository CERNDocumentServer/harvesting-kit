# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Set of utilities for the SCOAP3 project.
"""

import time
import sys
import traceback

from datetime import datetime
from os import listdir, rename, fdopen
from os.path import join, exists, walk
from tarfile import TarFile
from tempfile import mkdtemp, mkstemp
from urllib import urlretrieve
from zipfile import ZipFile
from xml.dom.minidom import parse

from invenio.errorlib import register_exception
from invenio.bibrecord import record_add_field, record_xml_output
from invenio.config import CFG_TMPSHAREDDIR, CFG_ETCDIR, CFG_LOGDIR
from invenio.shellutils import run_shell_command
from invenio.bibtask import task_low_level_submission
from invenio.contrast_out_utils import create_logger

CFG_SCOAP3DTDS_PATH = join(CFG_ETCDIR, 'scoap3dtds')

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


def xml_to_text(xml):
    if xml.nodeType == xml.TEXT_NODE:
        return xml.wholeText.encode('utf-8')
    elif 'mml:' in xml.nodeName:
        return xml.toxml().replace('mml:','').replace('xmlns:mml','xmlns').encode('utf-8')
    elif xml.hasChildNodes():
        for child in xml.childNodes:
            return ''.join(xml_to_text(child) for child in xml.childNodes)
    return ''


def get_value_in_tag(xml, tag):
    tag_elements = xml.getElementsByTagName(tag)
    if tag_elements:
        return xml_to_text(tag_elements[0])
    else:
        return ""


def get_attribute_in_tag(xml, tag, attr):
    tag_elements = xml.getElementsByTagName(tag)
    tag_attributes = [] 
    for tag_element in tag_elements:
            if tag_element.hasAttribute(attr):
                tag_attributes.append(tag_element.getAttribute(attr))
            else:
                # Dunno if it should be locked at this level
                lock_issue()
    return tag_attributes


def lock_issue():
    """
    Locks the issu in case of error.
    """
    # TODO
    print >> sys.stderr, "locking issue"


class ElsevierPackage(object):
    """
    This class is specialized in parsing an Elsevier package
    and creating a SCOAP3-compatible bibupload containing the original
    PDF, XML, and every possible metadata filled in.

    @param package_name: the path to a tar.gz file to expand and parse
    @param path: the actual path of an already expanded package.

    @note: either C{package_name} or C{path} must be passed to the constructor.
    """
    def __init__(self, package_name=None, path=None):
        self.package_name = package_name
        self.path = path
        self.found_articles = []
        self._found_issues = []
        self.logger = create_logger(join(CFG_LOGDIR, 'elsevier_harvesting_'+str(datetime.now())+'.log'))

        if not path and package_name:
            self._extract_package()
        elif not path and not package_name:
            print "Starting harves"
            from invenio.contrast_out import ContrastOutConnector
            self.conn = ContrastOutConnector(self.logger)
            self.conn.run()
        self._crawl_elsevier_and_find_main_xml()
        self._crawl_elsevier_and_find_issue_xml()
        self._build_doi_mapping()

    def _extract_package(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path = mkdtemp(prefix="scoap3", dir=CFG_TMPSHAREDDIR)
        self.logger.debug("Extracting package: %s" % (self.package_name,))
        TarFile.open(self.package_name).extractall(self.path)

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
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
        else:
            def visit(arg, dirname, names):
                if "main.xml" in names and "main.pdf" in names:
                    try:
                        self._normalize_article_dir_with_dtd(dirname)
                        self.found_articles.append(dirname)
                    except Exception, err:
                        register_exception()
                        print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
            walk(self.path, visit, None)

    def _crawl_elsevier_and_find_issue_xml(self):
        """
        Information about the current volume, issue, etc. is available in a file
        called issue.xml that is available in a higher directory.
        """
        self._found_issues = []
        if not self.path and not self.package_name:
            for issue in self.conn._get_issues():
                dirname = issue.rstrip('/issue.xml')
                try:
                    self._normalize_issue_dir_with_dtd(dirname)
                    self._found_issues.append(dirname)
                except Exception, err:
                    register_exception()
                    print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
        else:
            def visit(arg, dirname, names):
                if "issue.xml" in names:
                    try:
                        self._normalize_issue_dir_with_dtd(dirname)
                        self._found_issues.append(dirname)
                    except Exception, err:
                        register_exception()
                        print >> sys.stderr, "ERROR: can't normalize %s: %s" % (dirname, err)
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
            self.logger.error("It looks like the path %s does not contain an si510 or si520 issue.xml file" % path)
            raise ValueError("It looks like the path %s does not contain an si510 or si520 issue.xml file" % path)
        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, 'issue.xml'), join(path, 'resolved_issue.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))


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
            self.logger.error("It looks like the path %s does not contain an art520 or art501 main.xml file" % path)
            raise ValueError("It looks like the path %s does not contain an art520 or art501 main.xml file" % path)

        cmd_exit_code, cmd_out, cmd_err = run_shell_command("xmllint --format --loaddtd %s --output %s", (join(path, 'main.xml'), join(path, 'resolved_main.xml')))
        if cmd_err:
            self.logger.error("Error in cleaning %s: %s" % (join(path, 'issue.xml'), cmd_err))
            raise ValueError("Error in cleaning %s: %s" % (join(path, 'main.xml'), cmd_err))

    def _build_doi_mapping(self):
        self._dois = {}
        for path in self._found_issues:
            xml = parse(open(join(path, "resolved_issue.xml")))
            jid = get_value_in_tag(xml, "jid")
            journal = CFG_ELSEVIER_JID_MAP.get(jid, jid)
            issn = get_value_in_tag(xml, "ce:issn")
            volume = get_value_in_tag(xml, "vol-first")
            issue = get_value_in_tag(xml, "iss-first")
            year = get_value_in_tag(xml, "start-date")[:4]
            doi = get_value_in_tag(xml, "start-date")
            for included_item in xml.getElementsByTagName("ce:include-item"):
                doi = get_value_in_tag(included_item, "ce:doi")
                first_page = get_value_in_tag(included_item, "ce:first-page")
                last_page = get_value_in_tag(included_item, "ce:last-page")
                self._dois[doi] = (journal, issn, volume, issue, first_page, last_page, year)

    def _get_doi(self, xml):
        try:
            return get_value_in_tag(xml, "ce:doi")
        except Exception, err:
            print >> sys.stderr, "Can't find doi"

    def get_preprint_ids(self, xml):
        tag_elements = xml.getElementsByTagName("ce:preprint")
        preprint_ids = []
        if tag_elements:
            for tag_element in tag_elements:
                for child in tag_element.childNodes:
                    if child.nodeName == "ce:inter-ref":
                        try:
                            preprint_ids.append(child.getAttribute("xlink:href").encode())
                        except:
                            print >> sys.stderr, "Can't find arXive id"
        return preprint_ids

    def get_title(self, xml):
        try:
            return get_value_in_tag(xml, "ce:title")
        except Exception, err:
            print >> sys.stderr, "Can't find title"

    def get_abstract(self, xml):
        try:
            tmp = get_value_in_tag(xml.getElementsByTagName("ce:abstract-sec")[0], "ce:simple-para")
            return tmp
        except Exception, err:
            print >> sys.stderr, "Can't find abstract"

    def get_keywords(self, xml):
        try:
            return [get_value_in_tag(keyword, "ce:text") for keyword in xml.getElementsByTagName("ce:keyword")]
        except Exception, err:
            print >> sys.stderr, "Can't find keywords"

    def get_copyright(self, xml):
        try:
            return get_value_in_tag(xml, "ce:copyright")
        except Exception, err:
            print >> sys.stderr, "Can't find copyright"

    def get_authors(self, xml):
        authors = []
        for author in xml.getElementsByTagName("ce:author"):
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
                    tmp["cross_ref"].append(cross_ref.getAttribute("refid").encode('utf-8'))
            authors.append(tmp)
        affiliations = {}
        for affiliation in xml.getElementsByTagName("ce:affiliation"):
            aff_id = affiliation.getAttribute("id").encode('utf-8')
            text = get_value_in_tag(affiliation, "ce:textfn")
            affiliations[aff_id] = text
        implicit_affilations = True
        for author in authors:
            matching_ref = [ref for ref in author.get("cross_ref", []) if ref in affiliations]
            if matching_ref:
                implicit_affilations = False
                author["affiliation"] = []
                for i in xrange(0,len(matching_ref)):
                    author["affiliation"].append(affiliations[matching_ref[i]])
        if implicit_affilations and len(affiliations) > 1:
            print >> sys.stderr, "Implicit affiliations are used, but there's more than one affiliation: %s" % affiliations
        if implicit_affilations and len(affiliations) >= 1:
            for author in authors:
                author["affiliation"] = []
                for aff in affiliations.values():
                    author["affiliation"].append(aff)
        return authors

    def get_publication_information(self, xml):
        doi = self._get_doi(xml)
        try:
            return self._dois[doi] + (doi, )
        except:
            return ('', '', '', '', '', '', '', doi)

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ce:bib-reference"):
            label = get_value_in_tag(reference, "label")
            authors = []
            for author in reference.getElementsByTagName("sb:author"):
                given_name = get_value_in_tag(author, "ce:given-name")
                surname = get_value_in_tag(author, "ce:surname")
                if given_name:
                    name = "%s, %s" % (surname, given_name)
                else:
                    name = surname
                authors.append(name)
            doi = get_value_in_tag(reference, "ce:doi")
            issue = get_value_in_tag(reference, "sb:issue")
            page = get_value_in_tag(reference, "sb:first-page")
            title = get_value_in_tag(reference, "sb:maintitle")
            volume = get_value_in_tag(reference, "sb:volume-nr")
            year = get_value_in_tag(reference, "sb:date")[:4]
            references.append((label, authors, doi, issue, page, title, volume, year))
        return references

    def get_article(self, path):
        return parse(open(join(path, "resolved_main.xml")))

    def get_record(self, path):
        self.logger.info("Creating record: %s" % (path,))
        xml = self.get_article(path)
        rec = {}
        title = self.get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])
        record_add_field(rec, '260', subfields=[('c', time.strftime('%Y-%m-%d'))])
        journal, issn, volume, issue, first_page, last_page, year, doi = self.get_publication_information(xml)
        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        authors = self.get_authors(xml)
        first_author = True
        for author in authors:
            subfields = [('a', '%s, %s' % (author['surname'], author.get('given_name') or author.get('initials')))]
            if 'orcid' in author:
                subfields.append(('j', author['orcid']))
            if 'affiliation' in author:
                for aff in author["affiliation"]:
                    subfields.append(('u', aff))
            if first_author:
                record_add_field(rec, '100', subfields=subfields)
                first_author = False
            else:
                record_add_field(rec, '700', subfields=subfields)
        abstract = self.get_abstract(xml)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'), ('u', 'http://creativecommons.org/licenses/by/3.0/')])
        copyright = self.get_copyright(xml)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = self.get_keywords(xml)
        if keywords:
            for keyword in keywords:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
        record_add_field(rec, '773', subfields=[('p', journal), ('v', volume), ('n', issue), ('c', '%s-%s' % (first_page, last_page)), ('y', year)])

        # Temporarily disabled
        # references = self.get_references(xml)
        # for label, authors, doi, issue, page, title, volume, year in references:
        #     subfields = []
        #     if doi:
        #         subfields.append(('a', doi))
        #     for author in authors:
        #         subfields.append(('h', author))
        #     if issue:
        #         subfields.append(('n', issue))
        #     if label:
        #         subfields.append(('o', label))
        #     if page:
        #         subfields.append(('p', page))
        #     subfields.append(('s', '%s %s (%s) %s' % (title, volume, year, page)))
        #     if title:
        #         subfields.append(('t', title))
        #     if volume:
        #         subfields.append(('v', volume))
        #     if year:
        #         subfields.append(('y', year))
        #     if subfields:
        #         record_add_field(rec, '999', ind1='C', ind2='5', subfields=subfields)

        record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
        record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.xml'))])
        record_add_field(rec, '980', subfields=[('a', 'SCOAP3')])
        return record_xml_output(rec)

    def bibupload_it(self):
        self.logger.debug("Preparing bibupload.")
        fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_', dir=CFG_TMPSHAREDDIR)
        out = fdopen(fd, 'w')
        print >> out, "<collection>"
        for i, path in enumerate(self.found_articles):
            print path
            print >> out, self.get_record(path)
            print path, i + 1, "out of", len(self.found_articles)
        print >> out, "</collection>"
        out.close()
        task_low_level_submission("bibupload", "Elsevier", "-i", "-r", name)


def main():
    try:
        if len(sys.argv) == 2:
            path_or_package = sys.argv[1]
            if path_or_package.endswith(".tar"):
                els = ElsevierPackage(package_name=path_or_package)
            else:
                els = ElsevierPackage(path=path_or_package)
        else:
            els = ElsevierPackage()
        els.bibupload_it()
    except Exception, err:
        register_exception()
        print >> sys.stderr, "ERROR: Exception captured: %s" % err
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
