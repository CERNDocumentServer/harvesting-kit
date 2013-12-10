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

import sys
import logging

from invenio.config import CFG_LOGDIR
from os.path import join


def xml_to_text(xml):
    if xml.nodeType == xml.TEXT_NODE:
        return xml.wholeText.encode('utf-8')
    elif 'mml:' in xml.nodeName:
        return xml.toxml().replace('mml:', '').replace('xmlns:mml', 'xmlns').encode('utf-8')
    elif xml.hasChildNodes():
        for child in xml.childNodes:
            return ' '.join(''.join(xml_to_text(child) for child in xml.childNodes).split())
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


# Creates a logger object
def create_logger(publisher, filename=join(CFG_LOGDIR, 'scoap3_harvesting.log')):
    logger = logging.getLogger(publisher)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(filename=filename)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    return logger


def progress_bar(n):
    num = 0
    while num <= n:
        yield "\r%i%% [%s%s]" % (num/n*100, "="*num, '.'*(n-num))
        num += 1


def format_arxiv_id(arxiv_id):
    if arxiv_id and not "/" in arxiv_id and "arXiv" not in arxiv_id:
        return "arXiv:%s" % (arxiv_id,)
    else:
        return arxiv_id


class MD5Error(Exception):
    def __init__(self, value):
        self.value = value


class NoDOIError(Exception):
    def __init__(self, value):
        self.value = value


class NoNewFiles(Exception):
    def __init__(self, value=None):
        self.value = value
