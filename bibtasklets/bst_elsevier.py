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
Springer BibTaskLet
"""

from harvestingkit.elsevier_package import ElsevierPackage
from invenio.dbquery import run_sql
from invenio.bibtask import write_message


def bst_elsevier():
    els = ElsevierPackage()
    els.bibupload_it()

    prepare_package_table()
    prepare_doi_package_table()

    write_message(els.conn.packages_delivery)
    for p in els.conn.packages_delivery:
        name = p[0][:-1]
        date = p[1]
        if run_sql("SELECT name FROM package WHERE name=%s", (name, )):
            write_message("Package already exist: %s: %s" % ('Elsevier', name))
            continue
        else:
            write_message("New pacakge discovered for publisher %s: %s" % ('Elsevier', name))
            run_sql("INSERT INTO package(name, delivery_date) VALUES(%s, %s)", (name, date))

    for dp in els.doi_package_name_mapping:
        try:
            p_name, doi = dp
            write_message('%s %s' % (p_name, doi))
            p_id = run_sql("SELECT id FROM package WHERE name=%s", (p_name,))
            write_message(p_id)
            try:
                write_message("Adding doi to package: %d %s" % (p_id[0][0], doi))
                run_sql("INSERT INTO doi_package VALUES(%s, %s)", (p_id[0][0], doi))
            except Exception as e:
                write_message(e)
                write_message("This already exist: %d %s" % (p_id[0][0], doi))
        except Exception as e:
            write_message(e)


def prepare_package_table():
    return run_sql("""CREATE TABLE IF NOT EXISTS package (
        id mediumint NOT NULL AUTO_INCREMENT,
        name varchar(255) NOT NULL UNIQUE,
        delivery_date datetime NOT NULL,
        PRIMARY KEY doi(id),
        KEY (name)
    ) ENGINE=MyISAM;""")


def prepare_doi_package_table():
    return run_sql("""CREATE TABLE IF NOT EXISTS doi_package (
        package_id mediumint NOT NULL,
        doi varchar(255) NOT NULL,
        PRIMARY KEY doi_pacakge(package_id, doi),
        FOREIGN KEY (package_id)
            REFERENCES package(id)
            ON DELETE CASCADE,
        FOREIGN KEY (doi)
            REFERENCES doi(doi)
            ON DELETE CASCADE
    ) ENGINE=MyISAM;""")
