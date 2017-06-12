# -*- coding: utf-8 -*-
#
# This file is part of Harvesting Kit.
# Copyright (C) 2013, 2014, 2015, 2016, 2017 CERN.
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

"""Kit of tools to convert publisher XML (NLM/JATS) to MARCXML."""


from setuptools import setup, find_packages

setup(
    name="HarvestingKit",
    version="0.6.10",
    packages=find_packages(),
    package_data={'': ['data/*.xml']},
    data_files=[("dtds", ["dtds/ja5_art501.zip",
                          "dtds/ja5_art510.zip",
                          "dtds/ja5_art520.zip",
                          "dtds/ja5_art540.zip",
                          "dtds/si510.zip",
                          "dtds/si520.zip",
                          "dtds/si540.zip",
                          "dtds/A++V2.4.zip",
                          "dtds/jats-archiving-dtd-1.0.zip",
                          "dtds/journal-publishing-dtd-2.3.zip"])],
    install_requires=[
        "beautifulsoup4>=4.1.3",
        "Unidecode>=0.04.14",
        "argcomplete>=0.8.0",
        "httpretty>=0.8.3",
        "lxml>=3.1.2",
        "requests>=2.2.0",
        "six>=1.7.3",
        "python-dateutil>=1.5",
        "HTMLParser>=0.0.2",
    ],
    author="INSPIRE-HEP collaboration",
    author_email="admin@inspirehep.net",
    description=__doc__,
    license="GPLv2",
    url="https://github.com/inspirehep/harvesting-kit",
    test_suite="harvestingkit.tests",
    entry_points={
        'console_scripts': [
            'harvestingkit_cli = harvestingkit.harvestingkit_cli:main'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'Topic :: Text Processing',
        'Topic :: Text Processing :: Markup :: XML',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ]
)
