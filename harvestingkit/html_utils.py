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

from HTMLParser import HTMLParser

from harvestingkit.utils import escape_for_xml


class MathMLStripper(HTMLParser):

    """Special HTML stripper that allows MathML."""

    mathml_elements = set([
        'annotation', 'annotation-xml', 'maction', 'math',
        'merror', 'mfenced', 'mfrac', 'mi', 'mmultiscripts',
        'mn', 'mo', 'mover', 'mpadded',
        'mphantom', 'mprescripts', 'mroot', 'mrow', 'mspace', 'msqrt',
        'mstyle', 'msub', 'msubsup', 'msup', 'mtable', 'mtd', 'mtext',
        'mtr', 'munder', 'munderover', 'none', 'semantics'
    ])

    def __init__(self):
        """Set initial values."""
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        """Return representation of pure text data."""
        self.fed.append(d)

    def handle_starttag(self, tag, attrs):
        """Return representation of html start tag and attributes."""
        if tag in self.mathml_elements:
            final_attr = ""
            for key, value in attrs:
                final_attr += ' {0}="{1}"'.format(key, value)
            self.fed.append("<{0}{1}>".format(tag, final_attr))

    def handle_endtag(self, tag):
        """Return representation of html end tag."""
        if tag in self.mathml_elements:
            self.fed.append("</{0}>".format(tag))

    def handle_entityref(self, name):
        """Return representation of entities."""
        self.fed.append('&%s;' % name)

    def handle_charref(self, name):
        """Return representation of numeric entities."""
        self.fed.append('&#%s;' % name)

    def get_data(self):
        """Return all the stripped data."""
        return ''.join(self.fed)

    @classmethod
    def html_to_text(cls, html):
        """Return stripped HTML, keeping only MathML."""
        s = cls()
        s.feed(escape_for_xml(html))
        return s.get_data()
