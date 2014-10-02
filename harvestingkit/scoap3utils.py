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
Set of utilities for the SCOAP3 project.
"""

from __future__ import division

import sys
import logging
import time

from tarfile import TarFile
from zipfile import ZipFile
try:
    from invenio.errorlib import register_exception
except ImportError:
    register_exception = lambda a=1, b=2: True

from os.path import join

try:
    from invenio.config import CFG_LOGDIR
except ImportError:
    from distutils.sysconfig import get_python_lib
    CFG_LOGDIR = join(get_python_lib(),
                      "harvestingkit",
                      "log")
CFG_CROSSREF_DOIS_PER_REQUEST = 10
CFG_CROSSREF_API_URL = "http://doi.crossref.org/search/doi?"


def lock_issue():
    """
    Locks the issu in case of error.
    """
    # TODO
    print >> sys.stderr, "locking issue"


# Creates a logger object
def create_logger(publisher,
                  filename=join(CFG_LOGDIR, 'scoap3_harvesting.log'),
                  logging_level=logging.DEBUG):
    logger = logging.getLogger(publisher)
    formatter = logging.Formatter(('%(asctime)s - %(name)s - '
                                   '%(levelname)-8s - %(message)s'))

    fh = logging.FileHandler(filename=filename)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.setLevel(logging_level)

    return logger


def progress_bar(n):
    num = 0
    while num <= n:
        yield "%d [%s%s]" % (num/n*100, "="*num, '.'*(n-num))
        num += 1


class MD5Error(Exception):
    def __init__(self, value):
        self.value = value


class NoNewFiles(Exception):
    def __init__(self, value=None):
        self.value = value


class FileTypeError(Exception):
    def __init__(self, value=None):
        self.value = value


class MissingFFTError(Exception):
    def __init__(self, value=None):
        self.value = value


class LoginException(Exception):
    pass


class MissingTagException(Exception):
    pass


def get_remote_file_size(ftp_connector, filename, storage):

        def dir_callback(val):
            storage.append(val.split()[4])
        ftp_connector.dir(filename, dir_callback)


def check_pkgs_integrity(filelist, logger, ftp_connector,
                         timeout=120, sleep_time=10):
    """
    Checks if files are not being uploaded to server.
    @timeout - time after which the script will register an error.
    """
    ref_1 = []
    ref_2 = []
    i = 1
    print >> sys.stdout, "\nChecking packages integrity."
    for filename in filelist:
        # ref_1.append(self.get_remote_file_size(filename))
        get_remote_file_size(ftp_connector, filename, ref_1)
    print >> sys.stdout, "\nGoing to sleep for %i sec." % (sleep_time,)
    time.sleep(sleep_time)

    while sleep_time*i < timeout:
        for filename in filelist:
            # ref_2.append(self.get_remote_file_size(filename))
            get_remote_file_size(ftp_connector, filename, ref_2)
        if ref_1 == ref_2:
            print >> sys.stdout, "\nIntegrity OK:)"
            logger.info("Packages integrity OK.")
            break
        else:
            print >> sys.stdout, "\nWaiting %d time for itegrity..." % (i,)
            logger.info("\nWaiting %d time for itegrity..." % (i,))
            i += 1
            ref_1, ref_2 = ref_2, []
            time.sleep(sleep_time)
    else:
        not_finished_files = []
        for count, val1 in enumerate(ref_1):
            if val1 != ref_2[count]:
                not_finished_files.append(filelist[count])

        print >> sys.stdout, "\nOMG, OMG something wrong with integrity."
        logger.error("Integrity check faild for files %s"
                     % (not_finished_files,))


def extract_package(package_name, path, logger):
    try:
        if ".tar" in package_name:
            TarFile.open(package_name).extractall(path)
        elif ".zip" in package_name:
            ZipFile(package_name).extractall(path)
        else:
            raise FileTypeError("It's not a TAR or ZIP archive.")
    except Exception as err:
        register_exception(alert_admin=True,
                           prefix="Elsevier error extracting package.")
        logger.error("Error extraction package file: %s %s"
                     % (path, err))
