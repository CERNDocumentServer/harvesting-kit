# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Basic config for Harvesting Kit."""

import os

try:
    from invenio.config import CFG_ETCDIR
except ImportError:
    CFG_ETCDIR = os.path.join(os.environ.get(
        "VIRTUAL_ENV", "/tmp"), "etc/harvestingkit/"
    )


def _get_config_environment_variable():
    try:
        return os.environ['HARVESTINGKIT_CONFIG_PATH']
    except:
        return ''


def _get_current_virtualenv():
    return os.environ.get("VIRTUAL_ENV", "")


CFG_DTDS_PATH = os.path.join(CFG_ETCDIR, 'harvestingdtds')

CFG_POSSIBLE_CONFIG_PATHS = [_get_config_environment_variable(),
                             (_get_current_virtualenv()
                              + '/var/harvestingkit/user_config.cfg'),
                             '/usr/var/harvestingkit/user_config.cfg',
                             '/etc/harvestingkit/user_config.cfg']
CFG_CONFIG_PATH = '../user_config.cfg'

for loc in CFG_POSSIBLE_CONFIG_PATHS:
    if os.path.exists(loc):
        CFG_CONFIG_PATH = loc
        break

CFG_FTP_CONNECTION_ATTEMPTS = 3
CFG_FTP_TIMEOUT_SLEEP_DURATION = 2


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

COMMON_ACRONYMS = [
    'LHC',
    'CFT',
    'QCD',
    'QED',
    'QFT',
    'ABJM',
    'NLO',
    'LO',
    'NNLO',
    'IIB',
    'IIA',
    'MSSM',
    'NMSSM',
    'SYM',
    'WIMP',
    'ATLAS',
    'CMS',
    'ALICE',
    'RHIC',
    'DESY',
    'HERA',
    'CDF',
    'D0',
    'BELLE',
    'BABAR',
    'BFKL',
    'DGLAP',
    'SUSY',
    'QM',
    'UV',
    'IR',
    'BRST',
    'PET',
    'GPS',
    'NMR',
    'XXZ',
    'CMB',
    'LISA',
    'CPT',
    'KEK',
    'TRIUMF',
    'PHENIX',
    'VLBI',
    'NGC',
    'SNR',
    'HESS',
    'AKARI',
    'GALEX',
    'ESO',
    'J-PARC',
    'CERN',
    'XFEL',
    'FAIUR',
    'ILC',
    'CLIC',
    'SPS',
    'BNL',
    'CEBAF',
    'SRF',
    'LINAC',
    'HERMES',
    'ZEUS',
    'H1',
    'GRB'
]

OA_LICENSES = [
    r'^CC-BY',
    r'^https?://creativecommons.org/',
    r'^Creative Commons Attribution',
    r'^OA$',
    r'^Open Access$'
]
