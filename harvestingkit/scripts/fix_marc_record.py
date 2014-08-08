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
from __future__ import print_function
import re
import sys
import getopt
from xml.dom.minidom import parse


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


def fix_title_capitalization(title):
    words = []
    for word in title.split():
        if word.upper() != word:
            words.append(word)
        else:
            words.append(word.lower())
    title = " ".join(words)
    title = title[0].upper() + title[1:]
    return title


def main():
    usage = """
    save to file:
    python fix_name_capitalization.py marc_file.xml >> result_file.xml
    print to terminal:
    python fix_name_capitalization.py marc_file.xml
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        if len(args) > 1:
            raise getopt.GetoptError("Too many arguments given!!!")
        elif not args:
            raise getopt.GetoptError("Missing mandatory argument url_to_crawl")
    except getopt.GetoptError as err:
        print(str(err))  # will print something like "option -a not recognized"
        print(usage)
        sys.exit(2)
    filename = args[0]
    document = parse(filename)

    datafields = document.getElementsByTagName('datafield')
    # fix author names
    author_tags = []
    for tag in datafields:
        if tag.getAttribute('tag') in ['100', '700']:
            author_tags.append(tag)
    for tag in author_tags:
        for subfield in tag.getElementsByTagName('subfield'):
            if subfield.getAttribute('code') == 'a':
                author = ''
                for child in subfield.childNodes:
                    if child.nodeType == child.TEXT_NODE:
                        author += child.nodeValue
                if author:
                    lastname, givennames = author.split(',')
                    lastname, givennames = fix_name_capitalization(
                        lastname, givennames.split()
                    )
                    givennames = collapse_initials(givennames)
                    subfield.firstChild.nodeValue = "%s, %s" %\
                        (lastname, givennames)
    #fix title
    title_tags = []
    for tag in datafields:
        if tag.getAttribute('tag') in ['242', '245', '246', '247']:
            title_tags.append(tag)
    for tag in title_tags:
        for subfield in tag.getElementsByTagName('subfield'):
            if subfield.getAttribute('code') in ['a', 'b']:
                for child in subfield.childNodes:
                    if child.nodeType == child.TEXT_NODE:
                        title = child.nodeValue
                        title = fix_title_capitalization(title)
                        child.nodeValue = title
    print(document.toxml())


if __name__ == '__main__':
    main()
