from __future__ import division

import logging
import sys

from datetime import datetime
from functools import partial
from ftplib import FTP
from os.path import join, walk
from tarfile import TarFile
from tempfile import mkdtemp
from xml.dom.minidom import parseString, parse

from contrast_out_config import *
from invenio.config import CFG_TMPSHAREDDIR, CFG_LOGDIR
from scoap3utils import xml_to_text

class ContrastOutConnector(object):
    def __init__(self):
        self.ftp = None
        self.files_list = []
        self.retrieved_packages = {}
        self.retrieved_packages_unpacked = []
        self.path = None
        self.path_tar = None
        self.retrieved_packages_unpacked = []
        self.found_articles = []
        self.found_issues = []
        self.path_r_pkg = []
        self.logger = self._create_logger(join(CFG_LOGDIR, 'elsevier_harvesting_'+str(datetime.now())+'.log'))

    def _create_logger(self, name):
        logger = logging.getLogger('contrast_out_connector')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(filename=name)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(logging.DEBUG)
        return logger

    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        try:
            self.ftp = FTP(CFG_CONTRAST_OUT_URL)
            self.ftp.login(user=CFG_CONTRAST_OUT_LOGIN, passwd=CFG_CONTRAST_OUT_PASSWORD)
            self.logger.debug("Succesful connection to the Elsevier server")
        except:
            self.logger.error("Faild to connect to the Elsevier server.")

    def _get_file_listing(self, phrase=None):
        if phrase:
            self.files_list = filter(lambda x: phrase in x, self.ftp.nlst())
        else:
            self.files_list = self.ftp.nlst()
        return self.files_list

    def _download_file_listing(self):
        path_ready_pkg = mkdtemp(prefix="scoap3_ready_pkg", dir=CFG_TMPSHAREDDIR)
        # Prints stuff
        print >> sys.stdout, "\nDownloading %i files." % (len(self.files_list))
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for filename in self.files_list:
            self.logger.info("Downloading: %s" % (filename,))
            pkg_path = join(path_ready_pkg, filename)
            self.path_r_pkg.append(pkg_path)
            try:
                ready_file = open(pkg_path, 'wb')
                self.ftp.retrbinary('RETR %s' % (filename,), ready_file.write)
                ready_file.close()
            except:
                self.logger.error("Error downloading file: %s" % (filename,))
                print >> sys.stdout, "\nError downloading %s file!" % (filename,)
                print >> sys.stdout, sys.exc_info()
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()
        return self.path_r_pkg

    def _get_packages(self):
        # Prints stuff
        print >> sys.stdout, "\nRetrieving packages names."
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for pack in self.path_r_pkg:
            self.logger.info("Retrieved package name: %s" % (pack,))
            pack_xml = parse(pack)
            package_file = pack_xml.getElementsByTagName('dataset-package-file')
            for pf in package_file:
                filename = pf.getElementsByTagName('filename')[0]
                md5_val = pf.getElementsByTagName('md5')[0]
                self.retrieved_packages[xml_to_text(filename)] = xml_to_text(md5_val)
             # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

        return self.retrieved_packages

    def _download_tars(self):
        self.path_tar = mkdtemp(prefix="scoap3_tar", dir=CFG_TMPSHAREDDIR)

        # Prints stuff
        print >> sys.stdout, "\nDownloading %i tar packages." \
                 % (len(self.retrieved_packages))
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for filename in self.retrieved_packages.iterkeys():
            self.logger.info("Downloading tar package: %s" % (filename,))
            unpack_path = join(self.path_tar, filename)
            self.retrieved_packages_unpacked.append(unpack_path)
            try:
                tar_file = open(unpack_path, 'wb')
                self.ftp.retrbinary('RETR %s' % filename, tar_file.write)
                tar_file.close()
            except:
                self.logger.error("Error downloading tar file: %s" % (filename,))
                print >> sys.stdout, "\nError downloading %s file!" % (filename,)
                print >> sys.stdout, sys.exc_info()
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

        return self.retrieved_packages_unpacked

    def _check_md5(self):
        import hashlib

        for filename, md5 in self.retrieved_packages.iteritems():
            our_md5 = hashlib.md5(open(join(self.path_tar, filename)).read()).hexdigest()
            if our_md5 != md5:
                self.logger.error("MD5 error: %s" % (filename,))
                print >> sys.stdout, "Error in MD5 of %s" % (filename,)
                print >> sys.stdout, "oryginal: %s, ours: %s" % (md5, our_md5)

    def _extract_packages(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path_unpacked = mkdtemp(prefix="scoap3_package", dir=CFG_TMPSHAREDDIR)
        for path in self.retrieved_packages_unpacked:
            TarFile.open(path).extractall(self.path_unpacked)

        return self.path_unpacked

    def _get_issues(self):
        for name in self.files_list:
            dataset_link = join(self.path_unpacked, name.split('.')[0], 'dataset.xml')
            dataset_xml = parse(dataset_link)
            journal_issues = dataset_xml.getElementsByTagName('journal-issue')
            if journal_issues:
                for journal_issue in journal_issues:
                    filename = xml_to_text(journal_issue.getElementsByTagName('ml')[0].getElementsByTagName('pathname')[0])
                    self.logger.info("Found issue %s in %s." % (filename, name))
                    pathname = join(self.path_unpacked, name.split('.')[0], filename)
                    self.found_issues.append(pathname)
            else:
                def visit(arg, dirname, names):
                    print "Walking %s" %(dirname,)
                    if "issue.xml" in names:
                        self.found_issues.append(join(dirname,"issue.xml"))
                walk(join(self.path_unpacked, name.split('.')[0]), visit, None)
        return self.found_issues

    def _get_metadata_and_fulltex_dir(self):
        # Prints stuff
        print >> sys.stdout, "\nRetrieving journal items directories."
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for name in self.files_list:
            dataset_link = join(self.path_unpacked, name.split('.')[0], 'dataset.xml')

            dataset_xml = parse(dataset_link)
            journal_items = dataset_xml.getElementsByTagName('journal-item')
            for journal_item in journal_items:
                xml_pathname = join(self.path_unpacked, name.split('.')[0], xml_to_text(journal_item.getElementsByTagName('ml')[0].getElementsByTagName('pathname')[0]))
                pdf_pathname = join(self.path_unpacked, name.split('.')[0], xml_to_text(journal_item.getElementsByTagName('web-pdf')[0].getElementsByTagName('pathname')[0]))
                self.found_articles.append(dict(xml=xml_pathname, pdf=pdf_pathname))
                self.logger.info("Getting metadata and fulltex directories: %s." % (xml_pathname,))
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

        return self.found_articles

    def run(self):
        self.connect()
        self._get_file_listing('.ready')
        self._download_file_listing()
        self._get_packages()
        self._download_tars()
        self._check_md5()
        self._extract_packages()
        self._get_metadata_and_fulltex_dir()

    def _progress_bar(self, n):
        num = 0
        while num <= n:
            yield "\r%i%% [%s%s]" % (num/n*100, "="*num, '.'*(n-num))
            num += 1
