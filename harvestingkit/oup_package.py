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
from __future__ import print_function

import sys
import time

from datetime import datetime

from socket import timeout as socket_timeout_exception

from invenio.bibtask import task_low_level_submission
from invenio.config import (CFG_TMPSHAREDDIR,
                            CFG_PREFIX,
                            CFG_LOGDIR)
from invenio.errorlib import register_exception
from os import (listdir,
                fdopen,
                remove)
from configparser import load_config
from os.path import (join,
                     walk,
                     basename)
try:
    from invenio.config import CFG_OXFORD_DOWNLOADDIR
except ImportError:
    CFG_OXFORD_DOWNLOADDIR = join(CFG_PREFIX, "var", "data",
                                  "scoap3", "oxford")

from .ftp_utils import FtpHandler

from .scoap3utils import (LoginException,
                          NoNewFiles)
from .nlm_utils import NLMParser
from shutil import copy
from tempfile import mkstemp
from zipfile import ZipFile

from .config import (CFG_CONFIG_PATH,
                     CFG_DTDS_PATH,
                     CFG_FTP_CONNECTION_ATTEMPTS,
                     CFG_FTP_TIMEOUT_SLEEP_DURATION)
from .utils import create_logger

CFG_OXFORD_JATS_PATH = join(CFG_DTDS_PATH, 'journal-publishing-dtd-2.3.zip')

CFG_TAR_FILES = join(CFG_OXFORD_DOWNLOADDIR, "tar_files")
CFG_UNPACKED_FILES = join(CFG_OXFORD_DOWNLOADDIR, "unpacked_files")


class OxfordPackage(object):
    """
    This class is specialized in parsing an Oxford package
    and creating a SCOAP3-compatible bibupload containing the original
    PDF, XML, and every possible metadata filled in.

    @param package_name: the path to a tar.gz file to expand and parse
    @param path: the actual path of an already expanded package.

    @note: either C{package_name} or C{path} don't have to be passed to the
    constructor, in this case the Oxford server will be harvested.
    """
    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        for tried_connection_count in range(CFG_FTP_CONNECTION_ATTEMPTS):
            try:
                self.ftp = FtpHandler(self.config.OXFORD.URL,
                                      self.config.OXFORD.LOGIN,
                                      self.config.OXFORD.PASSWORD)
                self.logger.debug(("Successful connection to the "
                                   "Oxford University Press server"))
                return
            except socket_timeout_exception as err:
                self.logger.error(('Failed to connect %d of %d times. '
                                   'Will sleep for %d seconds and try again.')
                                  % (tried_connection_count+1,
                                     CFG_FTP_CONNECTION_ATTEMPTS,
                                     CFG_FTP_TIMEOUT_SLEEP_DURATION))
                time.sleep(CFG_FTP_TIMEOUT_SLEEP_DURATION)
            except Exception as err:
                self.logger.error(('Failed to connect to the Oxford '
                                   'University Press server. %s') % (err,))
                break

        raise LoginException(err)

    def _get_file_listing(self, phrase=None, new_only=True):
        if phrase:
            lambda_expression = lambda x: (phrase in x) or (x == "go.xml")
            self.files_list = filter(lambda_expression, self.ftp.ls()[0])
        else:
            self.files_list = self.ftp.ls()[0]
        if new_only:
            self.files_list = (set(self.files_list)
                               - set(listdir(CFG_TAR_FILES)))
        return self.files_list

    def _download_tars(self, check_integrity=True):
        self.retrieved_packages_unpacked = []
        # Prints stuff
        if self.files_list and 'go.xml' in self.files_list:
            ## If no 'go.xml' than we skip the task.
            if check_integrity:
                self.ftp.check_pkgs_integrity(self.files_list, self.logger)

            print("Downloading %i tar packages." % (len(self.files_list)))

            total_count = len(self.files_list)

            prefix = time.strftime("%Y%m%d%H%M%S-")
            for i, filename in enumerate(self.files_list, start=1):
                if filename == 'go.xml':
                    ## We don't download go.xml
                    continue
                self.logger.info("Downloading tar package %s of %s: %s"
                                 % (i, total_count, filename,))
                unpack_path = join(CFG_TAR_FILES, prefix + filename)
                self.retrieved_packages_unpacked.append(unpack_path)
                try:
                    self.ftp.download(filename, CFG_TAR_FILES)
                    current_location = join(CFG_TAR_FILES, filename)
                    desired_location = join(CFG_TAR_FILES, prefix + filename)
                    copy(current_location, desired_location)
                    self.packages_delivery.append((filename[0:-4],
                                                   datetime.now()))
                    remove(current_location)
                except:
                    self.logger.error("Error downloading tar file: %s"
                                      % (filename,))
                    print(sys.exc_info())

            return self.retrieved_packages_unpacked
        else:
            self.logger.info("No new packages to download.")
            raise NoNewFiles

    def __init__(self, package_name=None, path=None,
                 extract_nations=False):
        if package_name:
            if not package_name.endswith(".zip"):
                raise Exception('package_name variable requires a ZIP file.')

        self.package_name = package_name
        self.path = path
        self._dois = []
        self.articles_normalized = []
        self.logger = create_logger(
            "Oxford",
            filename=join(CFG_LOGDIR, 'scoap3_harvesting.log')
        )

        self.config = load_config(CFG_CONFIG_PATH, {'OXFORD': []})

        self.packages_delivery = []
        self.doi_package_name_mapping = []

        if not path and package_name:
            self.logger.info("Got package: %s" % (package_name,))
            self.path = self._extract_packages()
        elif not path and not package_name:
            print("Starting harvest")
            self.run()
        self._crawl_oxford_and_find_main_xml()
        self.extract_nations = extract_nations

    def run(self):
        try:
            self.connect()
            self._get_file_listing('.zip')
            self._download_tars()
        except LoginException as err:
            register_exception(alert_admin=True,
                               prefix=
                               ("Failed to connect to the "
                                "Oxford University Press server. %s") % (err,))
            return
        except NoNewFiles:
            return
        self._extract_packages()

    def _extract_packages(self):
        """
        Extract a package in a new directory.
        """
        if not hasattr(self, "retrieved_packages_unpacked"):
            self.retrieved_packages_unpacked = [self.package_name]
        for path in self.retrieved_packages_unpacked:
            package_name = basename(path)
            self.path_unpacked = join(CFG_UNPACKED_FILES,
                                      package_name.split('.')[0])
            self.logger.debug("Extracting package: %s"
                              % (path.split("/")[-1],))
            try:
                if "_archival_pdf" in self.path_unpacked:
                    self.path_unpacked = (self.path_unpacked
                                          .rstrip("_archival_pdf"))
                    ZipFile(path).extractall(join(self.path_unpacked,
                                                  "archival_pdfs"))
                else:
                    ZipFile(path).extractall(self.path_unpacked)
                #TarFile.open(path).extractall(self.path_unpacked)
            except Exception:
                register_exception(alert_admin=True,
                                   prefix="OUP error extracting package.")
                self.logger.error("Error extraction package file: %s"
                                  % (path,))

        if hasattr(self, "path_unpacked"):
            return self.path_unpacked

    def _crawl_oxford_and_find_main_xml(self):
        """
        A package contains several subdirectory corresponding to each article.
        An article is actually identified by the existence of a main.pdf and
        a main.xml in a given directory.
        """
        self.found_articles = []

        def visit(arg, dirname, names):
            files = [filename for filename in names if ".xml" in filename]
            if files:
                try:
                    for f in files:
                        self.found_articles.append(join(dirname, f))

                except Exception as err:
                    register_exception()
                    print("ERROR: can't normalize %s: %s" % (dirname, err),
                          file=sys.stderr)

        if hasattr(self, 'path_unpacked'):
            walk(self.path_unpacked, visit, None)
        elif self.path:
            walk(self.path, visit, None)
        else:
            self.logger.info("Nothing to do.")

    def bibupload_it(self):
        if self.found_articles:
            nlm_parser = NLMParser(self.extract_nations)
            self.logger.debug("Preparing bibupload.")
            fd, name = mkstemp(suffix='.xml', prefix='bibupload_scoap3_',
                               dir=CFG_TMPSHAREDDIR)
            out = fdopen(fd, 'w')
            print("<collection>", file=out)
            for i, path in enumerate(self.found_articles):
                try:
                    print(nlm_parser.get_record(path,
                                                publisher='Oxford',
                                                collection='SCOAP3',
                                                logger=self.logger),
                          file=out)

                    xml_doc = nlm_parser.get_article(path)
                    doi = nlm_parser.get_doi(xml_doc)
                    package_name = [x for x in path.split('/')
                                    if 'ptep_iss' in x]
                    if package_name:
                        self.doi_package_name_mapping.append((package_name[0],
                                                              doi))
                except Exception as err:
                    print(err, file=sys.stderr)
                    raise
                print(path, i + 1, "out of", len(self.found_articles))
            print("</collection>", file=out)
            out.close()
            task_low_level_submission("bibupload", "admin",
                                      "-N" "OUP", "-i", "-r", name)

    def empty_ftp(self):
        if self.found_articles:
            self.logger.info("Finishing UP. Emptying the FTP")
            for filename in self.files_list:
                self.logger.debug("Deleting %s" % filename)
                self.ftp.rm(filename)
