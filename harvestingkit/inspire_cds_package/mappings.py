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

"""Basic mapping between CDS/INSPIRE."""

import csv
import os

from pkg_resources import resource_filename

mappings = {
  "config": {
    "languages": [
      {
        "cds": "nno",
        "inspire": "Norwegian"
      },
      {
        "cds": "eng",
        "inspire": "English"
      },
      {
        "cds": "rom",
        "inspire": "Romany"
      },
      {
        "cds": "jpn",
        "inspire": "Japanese"
      },
      {
        "cds": "por",
        "inspire": "Portuguese"
      },
      {
        "cds": "ita",
        "inspire": "Italian"
      },
      {
        "cds": "ara",
        "inspire": "Arabic"
      },
      {
        "cds": "pol",
        "inspire": "Polish"
      },
      {
        "cds": "jap",
        "inspire": "Japanese"
      },
      {
        "cds": "tur",
        "inspire": "Turkish"
      },
      {
        "cds": "spa",
        "inspire": "Spanish"
      },
      {
        "cds": "glg",
        "inspire": "Galician"
      },
      {
        "cds": "arm",
        "inspire": "Armenian"
      },
      {
        "cds": "cze",
        "inspire": "Czech"
      },
      {
        "cds": "sue",
        "inspire": "Swedish"
      },
      {
        "cds": "est",
        "inspire": "Estonian"
      },
      {
        "cds": "che",
        "inspire": "Chechen"
      },
      {
        "cds": "fre",
        "inspire": "French"
      },
      {
        "cds": "scr",
        "inspire": "Serbo-Croatian"
      },
      {
        "cds": "chi",
        "inspire": "Chilean"
      },
      {
        "cds": "hrv",
        "inspire": "Croatian"
      },
      {
        "cds": "swe",
        "inspire": "Swedish"
      },
      {
        "cds": "ukr",
        "inspire": "Ukrainian"
      },
      {
        "cds": "ice",
        "inspire": "Icelandic"
      },
      {
        "cds": "lit",
        "inspire": "Lithuanian"
      },
      {
        "cds": "gre",
        "inspire": "Greek"
      },
      {
        "cds": "peo",
        "inspire": "Persian"
      },
      {
        "cds": "heb",
        "inspire": "Hebrew"
      },
      {
        "cds": "mul",
        "inspire": "Multiple"
      },
      {
        "cds": "kor",
        "inspire": "Korean"
      },
      {
        "cds": "fin",
        "inspire": "Finnish"
      },
      {
        "cds": "hun",
        "inspire": "Hungarian"
      },
      {
        "cds": "ser",
        "inspire": "Serbian"
      },
      {
        "cds": "ger",
        "inspire": "German"
      },
      {
        "cds": "rum",
        "inspire": "Romanian"
      },
      {
        "cds": "dan",
        "inspire": "Danish"
      },
      {
        "cds": "nob",
        "inspire": "Norwegian"
      },
      {
        "cds": "lat",
        "inspire": "Latin"
      },
      {
        "cds": "rus",
        "inspire": "Russian"
      },
      {
        "cds": "nor",
        "inspire": "Norwegian"
      },
      {
        "cds": "dut",
        "inspire": "Dutch"
      },
      {
        "cds": "slv",
        "inspire": "Slovenian"
      },
      {
        "cds": "esp",
        "inspire": "Spanish"
      },
      {
        "cds": "cat",
        "inspire": "Catalan"
      },
      {
        "cds": "srp",
        "inspire": "Serbian"
      },
      {
        "cds": "slo",
        "inspire": "Slovenian"
      },
      {
        "cds": "und",
        "inspire": "Undetermined"
      },
      {
        "cds": "tha",
        "inspire": "Thaiwanese"
      }
    ],
    "experiments": [
      {
        "cds": "CERN LHC---",
        "inspire": "CERN-LHC"
      },
      {
        "cds": "CERN LHC---ATLAS",
        "inspire": "CERN-LHC-ATLAS"
      },
      {
        "cds": "CERN LHC---CMS",
        "inspire": "CERN-LHC-CMS"
      },
      {
        "cds": "CERN LHC---LHCb",
        "inspire": "CERN-LHC-LHCb"
      },
      {
        "cds": "CERN LHC---ALICE",
        "inspire": "CERN-LHC-ALICE"
      },
      {
        "cds": "CERN LHC---TOTEM",
        "inspire": "CERN-LHC-TOTEM"
      },
      {
        "cds": "CERN LHC---LHCf",
        "inspire": "CERN-LHC-LHCf"
      },
      {
        "cds": "CERN LHC---MoEDAL",
        "inspire": "CERN-LHC-MoEDAL"
      },
      {
        "cds": "CERN PS---nTOF",
        "inspire": "CERN-nTOF"
      },
      {
        "cds": "---CAST",
        "inspire": "CERN-CAST"
      },
      {
        "cds": "CERN PS---nTOF",
        "inspire": "CERN-PS-nTOF"
      },
      {
        "cds": "CERN LEP---ALEPH",
        "inspire": "CERN-LEP-ALEPH"
      },
      {
        "cds": "CERN LEP---DELPHI",
        "inspire": "CERN-LEP-DELPHI"
      },
      {
        "cds": "CERN LEP---OPAL",
        "inspire": "CERN-LEP-OPAL"
      },
      {
        "cds": "CERN LEP---L3",
        "inspire": "CERN-LEP-L3"
      },
      {
        "cds": "CERN SPS---ICARUS CNGS2",
        "inspire": "ICARUS"
      },
      {
        "cds": "CERN SPS---OPERA CNGS1",
        "inspire": "OPERA"
      },
      {
        "cds": "---RD",
        "inspire": "CERN-RD-0"
      },
      {
        "cds": "CERN LHC---LHCf",
        "inspire": "CERN-LHC-LHCf"
      },
      {
        "cds": "CERN SPS---NA",
        "inspire": "CERN-NA-0"
      },
      {
        "cds": "CERN SPS---WA",
        "inspire": "CERN-WA-0"
      },
      {
        "cds": "DESY HERA---ZEUS",
        "inspire": "DESY-HERA-ZEUS"
      }
    ],
    "categories_cds": [
      {
        "cds": "General Relativity and Cosmology",
        "inspire": "Gravitation and Cosmology"
      },
      {
        "cds": "Detectors and Experimental Techniques",
        "inspire": "Instrumentation"
      },
      {
        "cds": "Accelerators and Storage Rings",
        "inspire": "Accelerators"
      },
      {
        "cds": "Computing and Computers",
        "inspire": "Computing"
      },
      {
        "cds": "Mathematical Physics and Mathematics",
        "inspire": "Math and Math Physics"
      },
      {
        "cds": "Astrophysics and Astronomy",
        "inspire": "Astrophysics"
      },
      {
        "cds": "Physics in General",
        "inspire": "General Physics"
      },
      {
        "cds": "Other",
        "inspire": "Other"
      },
      {
        "cds": "Particle Physics - Experiment",
        "inspire": "Experiment-HEP"
      },
      {
        "cds": "Particle Physics - Phenomenology",
        "inspire": "Phenomenology-HEP"
      },
      {
        "cds": "Particle Physics - Theory",
        "inspire": "Theory-HEP"
      },
      {
        "cds": "Particle Physics - Lattice",
        "inspire": "Lattice"
      },
      {
        "cds": "Nuclear Physics - Experiment",
        "inspire": "Experiment-Nucl"
      },
      {
        "cds": "Nuclear Physics - Theory",
        "inspire": "Theory-Nucl"
      },
      {
        "cds": "Quantum Technology",
        "inspire": "Quantum Physics"
      }
    ],
    "categories_inspire": [
      {
        "cds": "General Relativity and Cosmology",
        "inspire": "Gravitation and Cosmology"
      },
      {
        "cds": "General Theoretical Physics",
        "inspire": "General Physics"
      },
      {
        "cds": "Detectors and Experimental Techniques",
        "inspire": "Instrumentation"
      },
      {
        "cds": "Engineering",
        "inspire": "Instrumentation"
      },
      {
        "cds": "Accelerators and Storage Rings",
        "inspire": "Accelerators"
      },
      {
        "cds": "Computing and Computers",
        "inspire": "Computing"
      },
      {
        "cds": "Mathematical Physics and Mathematics",
        "inspire": "Math and Math Physics"
      },
      {
        "cds": "Astrophysics and Astronomy",
        "inspire": "Astrophysics"
      },
      {
        "cds": "Condensed Matter",
        "inspire": "General Physics"
      },
      {
        "cds": "General Theoretical Physics",
        "inspire": "General Physics"
      },
      {
        "cds": "Physics in General",
        "inspire": "General Physics"
      },
      {
        "cds": "Other",
        "inspire": "Other"
      },
      {
        "cds": "Chemical Physics and Chemistry",
        "inspire": "Other"
      },
      {
        "cds": "Information Transfer and Management",
        "inspire": "Other"
      },
      {
        "cds": "Commerce, Economics, Social Science",
        "inspire": "Other"
      },
      {
        "cds": "Biography, Geography, History",
        "inspire": "Other"
      },
      {
        "cds": "Science in General",
        "inspire": "Other"
      },
      {
        "cds": "Particle Physics - Experiment",
        "inspire": "Experiment-HEP"
      },
      {
        "cds": "Particle Physics - Phenomenology",
        "inspire": "Phenomenology-HEP"
      },
      {
        "cds": "Particle Physics - Theory",
        "inspire": "Theory-HEP"
      },
      {
        "cds": "Particle Physics - Lattice",
        "inspire": "Lattice"
      },
      {
        "cds": "Nuclear Physics - Experiment",
        "inspire": "Experiment-Nucl"
      },
      {
        "cds": "Nuclear Physics - Theory",
        "inspire": "Theory-Nucl"
      },
      {
        "cds": "Quantum Physics",
        "inspire": "Quantum Technology"
      }
    ],
  }
}


journals = []
journals_path = resource_filename('harvestingkit',
                                  'inspire_cds_package/journals_mappings.csv')
with open(journals_path, 'U') as journals_file:
    journals_mappings = csv.DictReader(journals_file)
    for journal in journals_mappings:
        journals.append(journal)

mappings['config']['journals'] = journals
