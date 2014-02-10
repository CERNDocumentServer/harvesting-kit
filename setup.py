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

import os

from setuptools import setup, find_packages
from invenio.config import CFG_ETCDIR, CFG_PYLIBDIR

dtd_path = os.path.join(CFG_ETCDIR, "harvestingdtd")
bibtasklet_path = os.path.join(CFG_PYLIBDIR, 'invenio', 'bibsched_tasklets')

req = open('requirements.txt','r')
requirements = []
for line in req:
  if line:
    requirements.append(line)
req.close()

setup(name="HarvestingKit",
      version="0.1",
      packages=find_packages(),
      data_files=[(bibtasklet_path, ["bibtasklets/bst_elsevier.py",
                                     "bibtasklets/bst_oxford.py",
                                     "bibtasklets/bst_springer.py"]),
                  (dtd_path, ["dtds/ja5_art501.zip",
                              "dtds/ja5_art510.zip",
                              "dtds/ja5_art520.zip",
                              "dtds/si510.zip",
                              "dtds/si520.zip",
                              "dtds/A++V2.4.zip",
                              "dtds/jats-archiving-dtd-1.0.zip",
                              "dtds/journal-publishing-dtd-2.3.zip"])],
      install_requires=requirements,
      author="CERN",
      author_email="admin@inspirehep.net",
      description="Kit containing scripts and utils for harvesting with Invenio Software.",
      license="GPLv2",
      url="https://github.com/inspirehep/harvesting-kit",
    )
