# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2013, 2014 CERN.
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

"""
Basic config for Harvesting Kit.
"""

import os
import warnings
from sys import executable

from invenio.config import CFG_ETCDIR


def _get_config_environment_variable():
    try:
        return os.environ['HARVESTINGKIT_CONFIG_PATH']
    except:
        return ''


def _get_current_virtualenv():
    path = executable.split(os.sep)
    return os.sep.join(path[:-2])


CFG_DTDS_PATH = os.path.join(CFG_ETCDIR, 'harvestingdtds')

CFG_POSSIBLE_CONFIG_PATHS = [_get_config_environment_variable(),
                             (_get_current_virtualenv()
                              + '/var/harvestingkit/user_config.cfg'),
                             '/etc/harvestingkit/user_config.cfg']
CFG_CONFIG_PATH = '../user_config.cfg'

for loc in CFG_POSSIBLE_CONFIG_PATHS:
    if os.path.exists(loc):
        CFG_CONFIG_PATH = loc
        break
else:
    warnings.warn("Could not find config.cfg")

CFG_FTP_CONNECTION_ATTEMPTS = 3
CFG_FTP_TIMEOUT_SLEEP_DURATION = 2
CFG_EDP_FULLTEXT_DIR = '/tmp/edp'
