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


def contrast_out_cmp(x, y):
    def get_val_type(x):
        val = x
        val_vtex = False
        val_type = None

        if "vtex" in val:
            val_vtex = True
            val = val.split('_')[0]
            val = val.strip("vtex")
        else:
            val = val[4:]
            for w in ["P", "S", "Q", "AB", "J", "R"]:
                if w in val:
                    if w is "P":
                        val_type = 1
                    if w is "Q":
                        val_type = 2
                    if w in ["S", "R"]:
                        val_type = 3
                    if w is "AB":
                        val_type = 4
                    if w is "J":
                        val_type = 5
                val = val.strip(w)

        return val, val_type, val_vtex

    x_number, x_type, x_vtex = get_val_type(x)
    y_number, y_type, y_vtex = get_val_type(y)

    if x_vtex or y_vtex:
        if x_vtex and not y_vtex:
            return 1
        elif not x_vtex and y_vtex:
            return -1
        elif x_vtex and y_vtex:
            if int(x_number) > int(y_number):
                return 1
            elif int(x_number) < int(y_number):
                return -1
            else:
                return 0
    else:
        if int(x_number) > int(y_number):
            return 1
        elif int(x_number) < int(y_number):
            return -1
        else:
            if int(x_type) > int(y_type):
                return 1
            elif int(x_type) < int(y_type):
                return -1
            else:
                return 0


def find_package_name(path):
    try:
        return [p_name for p_name in path.split('/') if "CERN" in p_name or "vtex" in p_name][0]
    except:
        return "unknown"
