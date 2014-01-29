# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
BibTasklet to discover new DOIs as they come by.
"""

import re
from datetime import datetime, timedelta

from invenio.bibtask import task_update_progress, write_message
from invenio.crossrefutils import get_all_modified_dois
from invenio.dbquery import run_sql


CFG_SCOAP3_DOIS = {
    "10.1016": re.compile(r"^%s|^%s" % (re.escape("10.1016/j.physletb."), re.escape("10.1016/j.nuclphysb."))), # Elsevier
    "10.1155": None, # Hindawi
    "10.1088": re.compile(r"^10\.1088\/(1674-1137|1475-7516|1367-2630)"), # IOPP,
    "10.5506": re.compile(r"^10\.5506\/APhysPolB\."), # Acta
    "10.1093": re.compile(r"^10\.1093\/ptep\/"), # Oxford
    "10.1140": re.compile(r"^10\.1140\/epjc\/"), # Springer EPJC
    "10.1007": re.compile(r"^10\.1007\/JHEP") # Springer Sissa
}

def prepate_doi_table():
    run_sql("""CREATE TABLE IF NOT EXISTS doi (
        doi varchar(255) NOT NULL,
        creation_date datetime NOT NULL,
        PRIMARY KEY doi(doi),
        KEY (creation_date)
    ) ENGINE=MyISAM;""")

def bst_doi_timestamp():
    prepate_doi_table()
    now = datetime.now()
    last_run = ((run_sql("SELECT max(creation_date) FROM doi")[0][0] or datetime(2014, 1, 1)) - timedelta(days=4)).strftime("%Y-%m-%d")
    write_message("Retrieving DOIs modified since %s" % last_run)
    for publisher, re_match in CFG_SCOAP3_DOIS.items():
        task_update_progress("Retrieving DOIs for %s" % publisher)
        write_message("Retriving DOIs for %s" % publisher)
        res = get_all_modified_dois(publisher, last_run, re_match, debug=True)
        for doi in res:
            if run_sql("SELECT doi FROM doi WHERE doi=%s", (doi, )):
                continue
            write_message("New DOI discovered for publisher %s: %s" % (publisher, doi))
            run_sql("INSERT INTO doi(doi, creation_date) VALUES(%s, %s)", (doi, now))
