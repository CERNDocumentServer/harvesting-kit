# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2015 CERN.
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

"""HTML utils."""

# HACK: this is needed to load local HTMLParser from Python 2.7
# in case Python 2.6 is used.
import sys

from harvestingkit.utils import escape_for_xml

_tmp_sys_path = sys.path
_new_sys_path = []
try:
    for path in sys.path:
        if ('dist-packages' in path) or ('site-packages' in path):
            _new_sys_path.append(path)
    _new_sys_path.extend(sys.path)
    sys.path = _new_sys_path
    from HTMLParser import HTMLParser
finally:
    sys.path = _tmp_sys_path


class MathMLParser(HTMLParser):

    """Special HTML stripper that allows MathML."""

    mathml_elements = set(['msline', 'mlongdiv', 'mstyle', 'mlabeledtr',
                           'mover', 'mglyph', 'msrow', 'mscarries', 'msgroup',
                           'mrow', 'annotation-xml', 'mphantom',
                           'mmultiscripts', 'msqrt', 'msub', 'mpadded',
                           'mtable', 'munder', 'math', 'msubsup', 'mfenced',
                           'mspace', 'mroot', 'maligngroup', 'msup', 'mfrac',
                           'munderover', 'mstack', 'annotation', 'semantics',
                           'none', 'mprescripts', 'mtr', 'mo', 'mn', 'mi',
                           'malignmark', 'mtd', 'ms', 'maction', 'merror',
                           'menclose', 'mscarry', 'mtext'])

    def __init__(self, escape_html=False):
        """Set initial values."""
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []
        self.escape_html = escape_html

    def handle_data(self, d):
        """Return representation of pure text data."""
        if self.escape_html:
            self.fed.append(escape_for_xml(d))
        else:
            self.fed.append(d)

    def handle_starttag(self, tag, attrs):
        """Return representation of html start tag and attributes."""
        final_attr = ""
        for key, value in attrs:
            final_attr += ' {0}="{1}"'.format(key, value)
        final_tag = "<{0}{1}>".format(tag, final_attr)
        if tag in self.mathml_elements:
            self.fed.append(final_tag)
        elif self.escape_html:
            self.fed.append(escape_for_xml(final_tag))

    def handle_endtag(self, tag):
        """Return representation of html end tag."""
        final_tag = "</{0}>".format(tag)
        if tag in self.mathml_elements:
            self.fed.append(final_tag)
        elif self.escape_html:
            self.fed.append(escape_for_xml(final_tag))

    def handle_entityref(self, name):
        """Return representation of entities."""
        final_entity = '&%s;' % name
        if self.escape_html:
            self.fed.append(escape_for_xml(final_entity))
        else:
            self.fed.append(final_entity)

    def handle_charref(self, name):
        """Return representation of numeric entities."""
        final_charref = '&#%s;' % name
        if self.escape_html:
            self.fed.append(escape_for_xml(final_charref))
        else:
            self.fed.append(final_charref)

    def get_data(self):
        """Return all the stripped data."""
        return ''.join(self.fed)

    @classmethod
    def html_to_text(cls, html):
        """Return stripped HTML, keeping only MathML."""
        s = cls()
        s.feed(html)
        unescaped_data = s.unescape(s.get_data())
        return escape_for_xml(unescaped_data, tags_to_keep=s.mathml_elements)
