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

from __future__ import division

import sys
import logging

from invenio.config import CFG_LOGDIR
from os.path import join


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
        yield "\r%d%% [%s%s]" % (num/n*100, "="*num, '.'*(n-num))
        num += 1


class MD5Error(Exception):
    def __init__(self, value):
        self.value = value


class NoNewFiles(Exception):
    def __init__(self, value=None):
        self.value = value
