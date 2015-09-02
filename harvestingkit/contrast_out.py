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

import sys
import time
from datetime import datetime

from socket import timeout as socket_timeout_exception

from os import listdir
from os.path import (join,
                     walk)
from tempfile import mkdtemp
from xml.dom.minidom import parse

try:
    from contrast_out_config import *
except ImportError:
    pass


try:
    from invenio.config import CFG_TMPSHAREDDIR
except ImportError:
    from distutils.sysconfig import get_python_lib
    CFG_TMPSHAREDDIR = join(get_python_lib(),
                            "harvestingkit",
                            "tmp")

try:
    from invenio.config import CFG_CONTRASTOUT_DOWNLOADDIR
except ImportError:
    from distutils.sysconfig import get_python_lib
    CFG_CONTRASTOUT_DOWNLOADDIR = join(get_python_lib(),
                                       "harvestingkit",
                                       "var", "data",
                                       "scoap3", "elsevier")

try:
    from invenio.errorlib import register_exception
except ImportError:
    register_exception = lambda a=1, b=2: True

from .ftp_utils import FtpHandler
from .scoap3utils import (MD5Error,
                          NoNewFiles,
                          LoginException,
                          MissingTagException,
                          extract_package as scoap3utils_extract_package)
from .contrast_out_utils import (contrast_out_cmp,
                                 find_package_name)
from .minidom_utils import xml_to_text

from configparser import load_config

from .config import (CFG_CONFIG_PATH,
                     CFG_FTP_CONNECTION_ATTEMPTS,
                     CFG_FTP_TIMEOUT_SLEEP_DURATION)

CFG_READY_PACKAGES = join(CFG_CONTRASTOUT_DOWNLOADDIR, "ready_pkgs")
CFG_TAR_FILES = join(CFG_CONTRASTOUT_DOWNLOADDIR, "tar_files")


class ContrastOutConnector(object):
    def __init__(self, logger):
        self.ftp = None
        self.files_list = []
        self.retrieved_packages = {}
        self.retrieved_packages_unpacked = []
        self.path = None
        self.retrieved_packages_unpacked = []
        self.found_articles = []
        self.found_issues = []
        self.path_r_pkg = []
        self.logger = logger
        self.packages_delivery = []

        self.config = load_config(CFG_CONFIG_PATH, {'ELSEVIER': []})

    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        for tried_connection_count in range(CFG_FTP_CONNECTION_ATTEMPTS):
            try:
                self.ftp = FtpHandler(self.config.ELSEVIER.URL,
                                      self.config.ELSEVIER.LOGIN,
                                      self.config.ELSEVIER.PASSWORD)
                self.logger.debug(('Successful connection to the '
                                   'Elsevier server'))
                return
            except socket_timeout_exception as err:
                self.logger.error(('Failed to connect %d of %d times. '
                                   'Will sleep for %d seconds and try again.')
                                  % (tried_connection_count+1,
                                     CFG_FTP_CONNECTION_ATTEMPTS,
                                     CFG_FTP_TIMEOUT_SLEEP_DURATION))
                time.sleep(CFG_FTP_TIMEOUT_SLEEP_DURATION)
            except Exception as err:
                self.logger.error(('Failed to connect to the '
                                   'Elsevier server. %s') % (err,))
                break

        raise LoginException(err)

    def _get_file_listing(self, phrase=None, new_only=True):
        if phrase:
            self.files_list = filter(lambda x: phrase in x, self.ftp.ls()[0])
        else:
            self.files_list = self.ftp.ls()[0]
        if new_only:
            self.files_list = (set(self.files_list)
                               - set(listdir(CFG_READY_PACKAGES)))

        return self.files_list

    def _download_file_listing(self):
        if self.files_list:
            # Prints stuff
            print("Downloading %i \".ready\" files." % (len(self.files_list)))
            # Create progrss bar
            total_count = len(self.files_list)

            for i, filename in enumerate(self.files_list, start=1):
                self.logger.info("Downloading %s of %s: %s"
                                 % (i, total_count, filename,))
                pkg_path = join(CFG_READY_PACKAGES, filename)
                self.path_r_pkg.append(pkg_path)
                try:
                    self.ftp.download(filename, CFG_READY_PACKAGES)
                except:
                    error_msg = "Error downloading file %s of %s: %s"
                    self.logger.error(error_msg % (i, total_count,
                                                   filename,))
                    print(sys.exc_info())
        else:
            self.logger.info("No new packages to download.")
            raise NoNewFiles

    def _get_packages(self):
        # Prints stuff
        print("Retrieving packages names.")
        # Create progrss bar
        total_count = len(self.files_list)

        for i, pack in enumerate(self.path_r_pkg, start=1):
            self.logger.info("Retrieved package name %s of %s: %s"
                             % (i, total_count, pack,))
            pack_xml = parse(pack)
            package_file = (pack_xml
                            .getElementsByTagName('dataset-package-file'))
            for pf in package_file:
                filename = pf.getElementsByTagName('filename')[0]
                md5_val = pf.getElementsByTagName('md5')[0]
                package_key = xml_to_text(filename)
                self.retrieved_packages[package_key] = xml_to_text(md5_val)

        return self.retrieved_packages

    def _download_tars(self, check_integrity=True):
        if check_integrity:
            self.ftp.check_pkgs_integrity(self.retrieved_packages, self.logger)

        print("Downloading %i tar packages." % (len(self.retrieved_packages)))
        # Create progrss bar
        total_count = len(self.files_list)

        for i, filename in enumerate(self.retrieved_packages.iterkeys(),
                                     start=1):
            self.logger.info("Downloading tar package %s of %s: %s"
                             % (i, total_count, filename,))
            unpack_path = join(CFG_TAR_FILES, filename)
            self.retrieved_packages_unpacked.append(unpack_path)
            try:
                self.ftp.download(filename, CFG_TAR_FILES)
                self.retrieved_packages_unpacked.append(unpack_path)
                self.packages_delivery.append((filename[0:-4], datetime.now()))
            except:
                register_exception(alert_admin=True,
                                   prefix="Elsevier package download failed.")
                self.logger.error("Error downloading tar file %s of %s: %s"
                                  % (i, total_count, filename,))
                print(sys.exc_info())

        return self.retrieved_packages_unpacked

    def _check_md5(self):
        import hashlib

        for filename, md5 in self.retrieved_packages.iteritems():
            our_md5 = hashlib.md5(open(join(CFG_TAR_FILES, filename))
                                  .read()).hexdigest()
            try:
                if our_md5 != md5:
                    raise MD5Error(filename)
            except MD5Error:
                register_exception(alert_admin=True,
                                   prefix="Elsevier MD5 error.")
                self.logger.error(("MD5 error: %s\n"
                                   "Original: %s, Ours: %s")
                                  % (filename, md5, our_md5,))

    def _extract_packages(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path_unpacked = mkdtemp(prefix="scoap3_package_",
                                     dir=CFG_TMPSHAREDDIR)
        for path in self.retrieved_packages_unpacked:
            scoap3utils_extract_package(path, self.path_unpacked, self.logger)

        return self.path_unpacked

    def _get_text_from_journal_item(self, journal_item, tag_list):
        try:
            for tag_name in tag_list:
                """
                This loop is a iterative assignment. It 'moves' through the tag
                tree of the journal item.
                """
                journal_item = journal_item.getElementsByTagName(tag_name)[0]
            return xml_to_text(journal_item)
        except Exception:
            raise MissingTagException("One of the searched tags (%s) "
                                      "is not valid." % (", ".join(tag_list)))

    def _get_issues(self):
        if "path_unpacked" in self.__dict__:
            for name in self.files_list:
                dataset_link = join(self.path_unpacked, name.split('.')[0],
                                    'dataset.xml')

                try:
                    dataset_xml = parse(dataset_link)
                except Exception:
                    register_exception(alert_admin=True, prefix=("Elsevier error reading dataset.xml file."))
                    error_msg = "Error reading dataset.xml file: %s"
                    self.logger.error(error_msg % (dataset_link,))
                    continue

                journal_issues = dataset_xml.getElementsByTagName('journal-issue')
                if journal_issues:
                    for journal_issue in journal_issues:
                        try:
                            tag_list = ['ml', 'pathname']
                            filename = (self
                                        ._get_text_from_journal_item(journal_issue,
                                                                     tag_list))
                            self.logger.info("Found issue %s in %s."
                                             % (filename, name))
                            pathname = join(self.path_unpacked,
                                            name.split('.')[0],
                                            filename)
                            self.found_issues.append(pathname)
                        except Exception as err:
                            register_exception(alert_admin=True,
                                               prefix=err.message)
                            self.logger.error("%s", err.message)
                            continue
                else:
                    def visit(arg, dirname, names):
                        if "issue.xml" in names:
                            self.found_issues.append(join(dirname, "issue.xml"))
                    walk(join(self.path_unpacked, name.split('.')[0]), visit, None)
        return self.found_issues

    def _get_metadata_and_fulltex_dir(self):
        print("Retrieving journal items directories.")

        total_count = len(self.files_list)

        for i, name in enumerate(self.files_list, start=1):
            dataset_link = join(self.path_unpacked, name.split('.')[0],
                                'dataset.xml')

            try:
                dataset_xml = parse(dataset_link)
            except Exception:
                register_exception(alert_admin=True,
                                   prefix=("Elsevier error reading "
                                           "dataset.xml file."))
                self.logger.error("Error reading dataset.xml file: %s"
                                  % (dataset_link,))
                continue

            journal_items = dataset_xml.getElementsByTagName('journal-item')
            self.logger.info(("%s of %s: Getting metadata and fulltex "
                              "directories for %i journal items.")
                             % (i, total_count, len(journal_items),))
            for journal_item in journal_items:
                try:
                    tag_list = ['ml', 'pathname']
                    xml_pathname = join(self.path_unpacked,
                                        name.split('.')[0],
                                        (self._get_text_from_journal_item(
                                            journal_item,
                                            tag_list)))
                    tag_list = ['web-pdf', 'pathname']
                    pdf_pathname = join(self.path_unpacked,
                                        name.split('.')[0],
                                        (self._get_text_from_journal_item(
                                            journal_item,
                                            tag_list)))

                    self.found_articles.append(dict(xml=xml_pathname,
                                                    pdf=pdf_pathname,
                                                    package=name.split('.'[0])))
                except MissingTagException as err:
                    register_exception(alert_admin=True,
                                       prefix=err.message)
                    self.logger.error("%s", err.message)
                    continue

            self.logger.info(("%s of %s: Found articles: %i.")
                             % (i, total_count, len(self.found_articles),))

        self.sort_results()
        return self.found_articles

    def sort_results(self):
        self.found_articles = sorted(self.found_articles,
                                     key=lambda x: find_package_name(x['xml']),
                                     cmp=contrast_out_cmp)

    def run(self, run_localy=False):
        if not run_localy:
            try:
                self.connect()
                self._get_file_listing('.ready')
                self._download_file_listing()
            except LoginException as err:
                register_exception(alert_admin=True,
                                   prefix=('Failed to connect to '
                                           'the Elsevier server. %s') % (err,))
                return
            except Exception as e:
                self.logger.info('No new packages to process')
                self.logger.info('Registered error: %s' % e)
                return
            self._get_packages()
            self._download_tars()
            self._check_md5()
        else:
            self.logger.info("Running on local files.")
            self.retrieved_packages_unpacked = []
            self.files_list = []
            for p in listdir(CFG_TAR_FILES):
                self.retrieved_packages_unpacked.append(join(CFG_TAR_FILES, p))
            for p in listdir(CFG_READY_PACKAGES):
                self.files_list.append(p.strip(".ready.xml"))
        self._extract_packages()
        self._get_metadata_and_fulltex_dir()
