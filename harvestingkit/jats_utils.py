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

import re
import sys
import time
from os import pardir
from os.path import (join,
                     dirname,
                     basename)
try:
    from invenio.errorlib import register_exception
except ImportError:
    register_exception = lambda a=1, b=2: True
from harvestingkit.minidom_utils import (get_value_in_tag,
                                         xml_to_text)
from harvestingkit.utils import (format_arxiv_id,
                                 add_nations_field)
from harvestingkit.bibrecord import (
    record_add_field,
    create_record,
    record_xml_output,
)
from xml.dom.minidom import parse


class JATSParser(object):
    def __init__(self, tag_to_remove=None, extract_nations=False):
        self.references = None
        self.tag_to_remove = tag_to_remove
        self.extract_nations = extract_nations

    def get_article(self, path):
        return parse(open(path))

    def get_title(self, xml):
        try:
            return get_value_in_tag(xml, "article-title", tag_to_remove=self.tag_to_remove)
        except Exception:
            print >> sys.stderr, "Can't find title"

    def get_issn(self, xml):
        issns = xml.getElementsByTagName('issn')
        ret = None

        for issn in issns:
            if issn.getAttribute("pub-type").encode('utf-8') == 'epub':
                ret = issn.getAttribute("pub-type").encode('utf-8')

        if not ret and issns:
            ret = xml_to_text(issns[0])

        return ret

    def get_date(self, xml):
        dates = xml.getElementsByTagName('pub-date')
        ret = None
        for date in dates:
            if date.getAttribute('pub-type').encode('utf-8') == 'epub':
                ret = get_value_in_tag(date, 'year')

        if not ret and dates:
            return dates[0]
        else:
            return ret

    def get_publication_information(self, xml):
        jid = get_value_in_tag(xml, "journal-title")
        journal = ""
        if "European Physical Journal" in jid:
            journal = "EPJC"

        try:
            art = xml.getElementsByTagName('article-meta')[0]
        except IndexError as err:
            register_exception()
            print >> sys.stderr, "ERROR: XML corrupted: %s" % err
            pass
        except Exception as err:
            register_exception()
            print >> sys.stderr, "ERROR: Exception captured: %s" % err
            pass

        issn = self.get_issn(art)
        volume = get_value_in_tag(art, "volume")
        issue = get_value_in_tag(art, "issue")
        year = self.get_date(art)
        first_page = get_value_in_tag(art, "fpage")
        last_page = get_value_in_tag(art, "lpage")
        doi = self.get_doi(art)

        return (journal, issn, volume, issue, first_page, last_page, year, doi)

    def get_doi(self, xml):
        ids = xml.getElementsByTagName('article-id')
        ret = ""
        for i in ids:
            if i.getAttribute('pub-id-type').encode('utf-8') == 'doi':
                ret = xml_to_text(i)

        if not ret:
            print >> sys.stdout, "Can't find DOI."
        return ret

    def _get_orcid(self, xml_author):
        try:
            contrib_id = xml_author.getElementsByTagName('contrib-id')[0]
            if contrib_id.getAttribute('contrib-id-type') == 'orcid':
                orcid_raw = xml_to_text(contrib_id)
                pattern = '\d\d\d\d-\d\d\d\d-\d\d\d\d-\d\d\d[\d|X]'
                return re.search(pattern, orcid_raw).group()
        except (IndexError, AttributeError):
            return None

    def get_authors(self, xml):
        authors = []
        for author in xml.getElementsByTagName("contrib"):
            # Springer puts colaborations in additional "contrib" tag so to
            # avoid having fake author with all affiliations we skip "contrib"
            # tag with "contrib" subtags.
            if author.getElementsByTagName("contrib"):
                continue
            tmp = {}
            surname = get_value_in_tag(author, "surname")
            if surname:
                tmp["surname"] = surname
            given_name = get_value_in_tag(author, "given-names")
            if given_name:
                tmp["given_name"] = given_name.replace('\n', ' ')
            if not surname and not given_name:
                tmp["name"] = get_value_in_tag(author, "string-name")
            # It's not there yet
            orcid = self._get_orcid(author)
            if orcid:
                tmp["orcid"] = 'ORCID:{0}'.format(orcid)

            # cross_refs = author.getElementsByTagName("ce:cross-ref")
            # if cross_refs:
            #     tmp["cross_ref"] = []
            #     for cross_ref in cross_refs:
            #         tmp["cross_ref"].append(cross_ref.getAttribute("refid").encode('utf-8'))
            tmp["affiliations_ids"] = []
            tmp["contact_ids"] = []

            xrefs = author.getElementsByTagName("xref")
            for x in xrefs:
                if x.getAttribute('ref-type').encode('utf-8') == 'aff':
                    tmp["affiliations_ids"].extend([a.encode('utf-8') for a in x.getAttribute('rid').split()])
                if x.getAttribute('ref-type').encode('utf-8') == 'corresp':
                    tmp["contact_ids"].extend([a.encode('utf-8') for a in x.getAttribute('rid').split()])

            authors.append(tmp)

        affiliations = {}
        for affiliation in xml.getElementsByTagName("aff"):
            aff_id = affiliation.getAttribute("id").encode('utf-8')
            # removes numbering in from affiliations
            text = re.sub(r'^(\d+,\ ?)', "", xml_to_text(affiliation, delimiter=", "))
            affiliations[aff_id] = text

        emails = {}
        for contact in xml.getElementsByTagName("corresp"):
            contact_id = contact.getAttribute("id").encode('utf-8')
            if contact.getElementsByTagName('email'):
                text = xml_to_text(contact.getElementsByTagName('email')[0])
                emails[contact_id] = text

        implicit_affilations = True
        for author in authors:
            matching_ref = [ref for ref in author.get("affiliations_ids") if ref in affiliations]
            if matching_ref:
                implicit_affilations = False
                author["affiliation"] = []
                for i in xrange(0, len(matching_ref)):
                    author["affiliation"].append(affiliations[matching_ref[i]])
            matching_contact = [cont for cont in author.get('contact_ids') if cont in emails]
            if matching_contact:
                author["email"] = emails[matching_contact[0]]

        if implicit_affilations and len(affiliations) > 1:
            print >> sys.stderr, "Implicit affiliations are used, but there are more than one affiliation: %s" % affiliations
        if implicit_affilations and len(affiliations) >= 1:
            for author in authors:
                author["affiliation"] = []
                for aff in affiliations.values():
                    author["affiliation"].append(aff)
        return authors

    def get_abstract(self, xml):
        try:
            return get_value_in_tag(xml, "abstract", tag_to_remove=self.tag_to_remove).replace("Abstract", "", 1)
        except Exception:
            print >> sys.stderr, "Can't find abstract"

    def get_copyright(self, xml, logger=None):
        tags = ["copyright-holder", "copyright-statement"]
        for tag in tags:
            if tag is "copyright-holder":
                ret = get_value_in_tag(xml, tag)
                if not ret:
                    if logger:
                        logger.info("Can't find copyright, trying different tag.")
                    print >> sys.stderr, "Can't find copyright, trying different tag."
                else:
                    return ret
            else:
                ret = get_value_in_tag(xml, tag)
                if not ret:
                    if logger:
                        logger.info("Can't find copyright")
                    print >> sys.stderr, "Can't find copyright"
                else:
                    ret = ret.split('.')
                    return ret[0]

    def get_keywords(self, xml):
        try:
            kwd_groups = xml.getElementsByTagName('kwd-group')
            pacs = []
            other = []
            for kwd_group in kwd_groups:
                if kwd_group.getAttribute('kwd-group-type').encode('utf-8') == "pacs":
                    pacs = [xml_to_text(keyword, tag_to_remove=self.tag_to_remove) for keyword in kwd_group.getElementsByTagName("kwd")]
                else:
                    other = [xml_to_text(keyword, tag_to_remove=self.tag_to_remove) for keyword in kwd_group.getElementsByTagName("kwd")]
            return {"pacs": pacs, "other": other}
        except Exception:
            print >> sys.stderr, "Can't find keywords"

    def get_ref_link(self, xml, name):
        links = xml.getElementsByTagName('ext-link')
        ret = None
        for link in links:
            if name in link.getAttribute("xlink:href").encode('utf-8'):
                ret = xml_to_text(link).strip()
        if not ret:
            links = xml.getElementsByTagName('elocation-id')
            for link in links:
                if name in link.getAttribute("content-type").encode('utf-8'):
                    ret = xml_to_text(link).strip()
        return ret

    def get_page_count(self, xml):
        counts = xml.getElementsByTagName("counts")
        if counts:
            page_count = counts[0].getElementsByTagName("page-count")
            if page_count:
                return page_count[0].getAttribute("count").encode('utf-8')
            else:
                return None
        else:
            return None

    def get_publication_date(self, xml, logger=None):
        date_xmls = xml.getElementsByTagName('pub-date')
        day = None
        month = None
        year = None
        if date_xmls:
            for date_xml in date_xmls:
                if date_xml.hasAttribute('pub-type'):
                    if date_xml.getAttribute('pub-type') == "epub":
                        day = get_value_in_tag(date_xml, "day")
                        month = get_value_in_tag(date_xml, "month")
                        year = get_value_in_tag(date_xml, "year")
                if not year:
                    day = get_value_in_tag(date_xml, "day")
                    month = get_value_in_tag(date_xml, "month")
                    year = get_value_in_tag(date_xml, "year")
            if logger:
                logger.info('%s-%s-%s' % (year, month, day))
            return '%s-%s-%s' % (year, month, day)
        else:
            print >> sys.stderr, "Can't find publication date. Using 'today'."
            if logger:
                logger.info("Can't find publication date. Using 'today'.")
            return time.strftime('%Y-%m-%d')

    def get_references(self, xml):
        references = []
        for reference in xml.getElementsByTagName("ref"):
            plain_text = None
            try:
                ref_type = reference.getElementsByTagName('mixed-citation')[0]
                ref_type = ref_type.getAttribute('publication-type').encode('utf-8')
            except:
                ref_type = reference.getElementsByTagName('citation')[0]
                ref_type = ref_type.getAttribute('publication-type').encode('utf-8')
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
                try:
                    plain_text = get_value_in_tag(reference,
                                                  "mixed-citation",
                                                  tag_to_remove=self.tag_to_remove)
                except:
                    plain_text = get_value_in_tag(reference,
                                                  "citation",
                                                  tag_to_remove=self.tag_to_remove)
            references.append((label, authors, doi,
                               issue, page, page_last,
                               title, volume, year,
                               ext_link, plain_text))
        self.references = references

    def get_record(self, f_path, publisher=None, collection=None, logger=None):
        xml = self.get_article(f_path)
        rec = create_record()
        title = self.get_title(xml)
        if title:
            record_add_field(rec, '245', subfields=[('a', title)])

        record_add_field(rec, '260', subfields=[('c', self.get_publication_date(xml, logger))])
        journal, issn, volume, issue, first_page, last_page, year, doi = self.get_publication_information(xml)

        if logger:
            logger.info("Creating record: %s %s" % (join(f_path, pardir), doi))

        if doi:
            record_add_field(rec, '024', ind1='7', subfields=[('a', doi), ('2', 'DOI')])
        authors = self.get_authors(xml)
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

        page_count = self.get_page_count(xml)
        if page_count:
            record_add_field(rec, '300', subfields=[('a', page_count)])
        abstract = self.get_abstract(xml)
        if abstract:
            record_add_field(rec, '520', subfields=[('a', abstract), ('9', publisher)])
        record_add_field(rec, '540', subfields=[('a', 'CC-BY-3.0'), ('u', 'http://creativecommons.org/licenses/by/3.0/')])
        copyright = self.get_copyright(xml, logger)
        if copyright:
            record_add_field(rec, '542', subfields=[('f', copyright)])
        keywords = self.get_keywords(xml)
        if keywords['pacs']:
            for keyword in keywords['pacs']:
                record_add_field(rec, '084', ind1='1', subfields=[('a', keyword), ('9', 'PACS')])
        if keywords['other']:
            for keyword in keywords['other']:
                record_add_field(rec, '653', ind1='1', subfields=[('a', keyword), ('9', 'author')])
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
        # record_add_field(rec, 'FFT', subfields=[('a', join(path, 'main.pdf'))])
        pdf_path = join(dirname(f_path), 'BodyRef', 'PDF', basename(f_path)[:-len('_nlm.xml')] + '.pdf')
        try:
            open(pdf_path)
            record_add_field(rec, 'FFT', subfields=[('a', pdf_path), ('n', 'main'), ('f', '.pdf;pdfa')])
        except:
            register_exception(alert_admin=True)
            logger.error("No PDF for paper: %s" % (doi,))
        record_add_field(rec, 'FFT', subfields=[('a', f_path), ('n', 'main')])
        extra_subfields = []
        if collection:
            extra_subfields.append(('a', collection))
        if publisher:
            extra_subfields.append(('b', publisher))
        record_add_field(rec, '980', subfields=extra_subfields)
        return record_xml_output(rec)
