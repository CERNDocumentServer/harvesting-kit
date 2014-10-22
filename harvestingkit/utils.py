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

import re
import htmlentitydefs
import requests
import subprocess

from lxml import etree
from unidecode import unidecode

NATIONS_DEFAULT_MAP = {"Algeria": "Algeria",
                       "Argentina": "Argentina",
                       "Armenia": "Armenia",
                       "Australia": "Australia",
                       "Austria": "Austria",
                       "Azerbaijan": "Azerbaijan",
                       "Belarus": "Belarus",
                       ##########BELGIUM########
                       "Belgium": "Belgium",
                       "Belgique": "Belgium",
                       #######################
                       "Bangladesh": "Bangladesh",
                       "Brazil": "Brazil",
                       "Bulgaria": "Bulgaria",
                       "Canada": "Canada",
                       ##########CERN########
                       "CERN": "CERN",
                       "Cern": "CERN",
                       #######################
                       "Chile": "Chile",
                       ##########CHINA########
                       "China (PRC)": "China",
                       "PR China": "China",
                       "China": "China",
                       #######################
                       "Colombia": "Colombia",
                       "Costa Rica": "Costa Rica",
                       "Cuba": "Cuba",
                       "Croatia": "Croatia",
                       "Cyprus": "Cyprus",
                       "Czech Republic": "Czech Republic",
                       "Denmark": "Denmark",
                       "Egypt": "Egypt",
                       "Estonia": "Estonia",
                       "Finland": "Finland",
                       "France": "France",
                       "Georgia": "Georgia",
                       ##########GERMANY########
                       "Germany": "Germany",
                       "Deutschland": "Germany",
                       #######################
                       "Greece": "Greece",
                       ##########HONG KONG########
                       "Hong Kong": "Hong Kong",
                       "Hong-Kong": "Hong Kong",
                       #######################
                       "Hungary": "Hungary",
                       "Iceland": "Iceland",
                       "India": "India",
                       "Indonesia": "Indonesia",
                       "Iran": "Iran",
                       "Ireland": "Ireland",
                       "Israel": "Israel",
                       ##########ITALY########
                       "Italy": "Italy",
                       "Italia": "Italy",
                       #######################
                       "Japan": "Japan",
                       ##########SOUTH KOREA########
                       "Korea": "South Korea",
                       "Republic of Korea": "South Korea",
                       "South Korea": "South Korea",
                       #######################
                       "Lebanon": "Lebanon",
                       "Lithuania": "Lithuania",
                       "México": "México",
                       "Montenegro": "Montenegro",
                       "Morocco": "Morocco",
                       ##########NETHERLANDS########
                       "Netherlands": "Netherlands",
                       "The Netherlands": "Netherlands",
                       #######################
                       "New Zealand": "New Zealand",
                       "Norway": "Norway",
                       "Pakistan": "Pakistan",
                       "Poland": "Poland",
                       "Portugal": "Portugal",
                       "Romania": "Romania",
                       ##########RUSSIA########
                       "Russia": "Russia",
                       "Russian Federation": "Russia",
                       #######################
                       "Saudi Arabia": "Saudi Arabia",
                       "Serbia": "Serbia",
                       "Singapore": "Singapore",
                       "Slovak Republic": "Slovakia",
                       ##########SLOVAKIA########
                       "Slovakia": "Slovakia",
                       "Slovenia": "Slovenia",
                       #######################
                       "South Africa": "South Africa",
                       "Spain": "Spain",
                       "Sweden": "Sweden",
                       "Switzerland": "Switzerland",
                       "Taiwan": "Taiwan",
                       "Thailand": "Thailand",
                       "Tunisia": "Tunisia",
                       "Turkey": "Turkey",
                       "Ukraine": "Ukraine",
                       ##########ENGLAND########
                       "United Kingdom": "UK",
                       "UK": "UK",
                       #######################
                       "England": "England",
                       ##########USA########
                       "United States of America": "USA",
                       "United States": "USA",
                       "USA": "USA",
                       #######################
                       "Uruguay": "Uruguay",
                       "Uzbekistan": "Uzbekistan",
                       "Venezuela": "Venezuela",
                       ##########VIETNAM########
                       "Vietnam": "Vietnam",
                       "Viet Nam": "Vietnam",
                       #######################
                       #########other#########
                       "Peru": "Peru",
                       "Kuwait": "Kuwait",
                       "Sri Lanka": "Sri Lanka",
                       "Kazakhstan": "Kazakhstan",
                       "Mongolia": "Mongolia",
                       "United Arab Emirates": "United Arab Emirates",
                       "Malaysia": "Malaysia",
                       "Qatar": "Qatar",
                       "Kyrgyz Republic": "Kyrgyz Republic",
                       "Jordan": "Jordan"}


def create_record():
    """Return a new XML document."""
    return etree.Element("record")


def record_add_field(rec, tag, ind1='', ind2='', subfields=[],
                     controlfield_value=''):
    """Add a MARCXML datafield as a new child to a XML document."""
    if controlfield_value:
        doc = etree.Element("controlfield",
                            attrib={
                                "tag": tag,
                            })
        doc.text = controlfield_value
    else:
        doc = etree.Element("datafield",
                            attrib={
                                "tag": tag,
                                "ind1": ind1,
                                "ind2": ind2,
                            })
        for code, value in subfields:
            field = etree.SubElement(doc, "subfield", attrib={"code": code})
            try:
                # In order to be parsed it needs to be proper XML
                parse_value = "<dummy>{0}</dummy>".format(escape_for_xml(value))
                sub_tree = etree.fromstring(parse_value)
                field.append(sub_tree)
            except etree.XMLSyntaxError:
                # Not sub XML
                field.text = value
    rec.append(doc)
    return rec


def record_xml_output(rec, pretty=True):
    """Given a document, return XML prettified."""
    # FIXME: make the dummy stuff go away - so far it works!(tm) tho
    ret = etree.tostring(rec, xml_declaration=False).replace("<dummy>", "").replace("</dummy>", "")

    if pretty:
        # We are doing our own prettyfication as etree pretty_print is too insane.
        ret = ret.replace('</datafield>', '  </datafield>\n')
        ret = re.sub(r'<datafield(.*?)>', r'  <datafield\1>\n', ret)
        ret = ret.replace('</subfield>', '</subfield>\n')
        ret = ret.replace('<subfield', '    <subfield')
        ret = ret.replace('record>', 'record>\n')

    # First we bring back most entities, but not &amp; and friends.
    return unescape(ret)


def escape_for_xml(data):
    """Transform & and < to XML valid &amp; and &lt."""
    data = re.sub("&(?!(amp|lt|gt);)", "&amp;", data)
    data = re.sub("<(?=[\=\d\.\s])", "&lt;", data)
    return data


def unescape(text):
    """Remove HTML or XML character references and entities from a text string.

    NOTE: Does not remove &amp; &lt; and &gt;.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    """
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        elif text[1:-1] not in ("gt", "lt", "amp"):
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


def format_arxiv_id(arxiv_id, INSPIRE=False):
    if arxiv_id and not "/" in arxiv_id and "arXiv" not in arxiv_id:
        return "arXiv:%s" % (arxiv_id,)
    elif INSPIRE and arxiv_id and not '.' in arxiv_id \
            and arxiv_id.lower().startswith('arxiv:'):
        return arxiv_id[6:]
    else:
        return arxiv_id


def collapse_initials(name):
    """ Removes the space between initials.
        eg T. A. --> T.A."""
    if len(name.split()) > 1:
        name = re.sub(r'([A-Z]\.) +(?=[A-Z]\.)', r'\1', name)
    return name


def fix_name_capitalization(lastname, givennames):
    """ Converts capital letters to lower keeps first letter capital. """
    if '-' in lastname:
        names = lastname.split('-')
        names = map(lambda a: a[0] + a[1:].lower(), names)
        lastname = '-'.join(names)
    else:
        lastname = lastname[0] + lastname[1:].lower()
    names = []
    for name in givennames:
        names.append(name[0] + name[1:].lower())
    givennames = ' '.join(names)
    return lastname, givennames


def fix_journal_name(journal, knowledge_base):
    """ Converts journal name to Inspire's short form """
    if not journal:
        return '', ''
    if not knowledge_base:
        return '', ''
    if len(journal) < 2:
        return journal, ''
    volume = ''
    if (journal[-1] <= 'Z' and journal[-1] >= 'A') \
            and (journal[-2] == '.' or journal[-2] == ' '):
        volume += journal[-1]
        journal = journal[:-1]
    try:
        journal = journal.strip()
        journal = knowledge_base[journal.upper()].strip()
    except KeyError:
        try:
            journal = knowledge_base[journal].strip()
        except KeyError:
            pass
    journal = journal.replace('. ', '.')
    return journal, volume


def add_nations_field(authors_subfields):
    result = []
    for field in authors_subfields:
        if field[0] == 'v':
            values = [x.replace('.', '') for x in field[1].split(', ')]
            possible_affs = filter(lambda x: x is not None,
                                   map(NATIONS_DEFAULT_MAP.get, values))
            if 'CERN' in possible_affs and 'Switzerland' in possible_affs:
                # Don't use remove in case of multiple Switzerlands
                possible_affs = [x for x in possible_affs
                                 if x != 'Switzerland']

            result.extend(possible_affs)

    result = sorted(list(set(result)))

    if result:
        authors_subfields.extend([('w', res) for res in result])
    else:
        authors_subfields.append(('w', 'HUMAN CHECK'))


def fix_dashes(string):
    string = string.replace(u'\u05BE', '-')
    string = string.replace(u'\u1806', '-')
    string = string.replace(u'\u2E3A', '-')
    string = string.replace(u'\u2E3B', '-')
    string = unidecode(string)
    return re.sub(r'--+', '-', string)


def download_file(from_url, to_filename, chunk_size=1024 * 8, retry_count=3):
    """Download URL to a file."""
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_count)
    session.mount(from_url, adapter)
    response = session.get(from_url, stream=True)
    with open(to_filename, 'wb') as fd:
        for chunk in response.iter_content(chunk_size):
            fd.write(chunk)
    return to_filename


def run_shell_command(commands, **kwargs):
    """Run a shell command."""
    p = subprocess.Popen(commands,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         **kwargs)
    output, error = p.communicate()
    return p.returncode, output, error
