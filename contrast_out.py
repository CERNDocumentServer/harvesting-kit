from __future__ import division

import sys

from functools import partial
from ftplib import FTP
from os.path import join
from tarfile import TarFile
from tempfile import mkdtemp
from xml.dom.minidom import parseString, parse

from contrast_out_config import *
from invenio.config import CFG_TMPSHAREDDIR
from scoap3utils import xml_to_text

class ContrastOutConnector(object):
    def __init__(self):
        self.ftp = None
        self.files_list = []
        self.ready_xml = []
        self.a = {}
        self.retrieved_packages = {}
        self.retrieved_packages_unpacked = []
        self.path = None
        self.path_tar = None
        self.retrieved_packages_unpacked = []
        self.found_articles = []

    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        self.ftp = FTP(CFG_CONTRAST_OUT_URL)
        self.ftp.login(user=CFG_CONTRAST_OUT_LOGIN, passwd=CFG_CONTRAST_OUT_PASSWORD)

    def _get_file_listing(self, phrase=None):
        if phrase:
            self.files_list = filter(lambda x: phrase in x, self.ftp.nlst())
        else:
            self.files_list = self.ftp.nlst()

    def _read_file_listing(self):
        # Prints stuff
        print >> sys.stdout, "\nReading %i files." % (len(self.files_list))
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for f in self.files_list:
            self.a[f] = ""
            self.ftp.retrlines('RETR %s' % (f,), partial(self._add_to_a, f))
            self.ready_xml.append(parseString(self.a[f]))
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

    def _get_packages(self):
        # Prints stuff
        print >> sys.stdout, "\nRetrieving packages names."
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for pack in self.ready_xml:
            package_file = pack.getElementsByTagName('dataset-package-file')
            for pf in package_file:
                filename = pf.getElementsByTagName('filename')[0]
                md5_val = pf.getElementsByTagName('md5')[0]
                self.retrieved_packages[xml_to_text(filename)] = xml_to_text(md5_val)
             # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

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
            try:
                unpack_path = join(self.path_tar, filename)
                self.retrieved_packages_unpacked.append(unpack_path)
                tar_file = open(unpack_path, 'wb')
                self.ftp.retrbinary('RETR %s' % filename, tar_file.write)
                tar_file.close()
            except:
                print >> sys.stdout, "\nError downloading %s file!" % (filename,)
                print >> sys.stdout, sys.exc_info()
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

    def _check_md5(self):
        import hashlib

        for filename, md5 in self.retrieved_packages.iteritems():
            our_md5 = hashlib.md5(open(join(self.path_tar, filename)).read()).hexdigest()
            if our_md5 != md5:
                print >> sys.stdout, "Error in MD5 of %s" % (filename,)
                print >> sys.stdout, "oryginal: %s, ours: %s" % (md5, our_md5)

    def _extract_packages(self):
        """
        Extract a package in a new temporary directory.
        """
        self.path_unpacked = mkdtemp(prefix="scoap3_package", dir=CFG_TMPSHAREDDIR)
        for path in self.retrieved_packages_unpacked:
            TarFile.open(path).extractall(self.path_unpacked)

    def _get_metadata_and_fulltex_dir(self):
        # Prints stuff
        print >> sys.stdout, "\nRetrieving jurnal items directories."
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for name in self.files_list:
            dataset_link = join(self.path_unpacked, name.split('.')[0], 'dataset.xml')

            dataset_xml = parse(dataset_link)
            jurnal_items = dataset_xml.getElementsByTagName('journal-item')
            for jurnal_item in jurnal_items:
                xml_pathname = join(self.path_unpacked, name.split('.')[0], xml_to_text(jurnal_item.getElementsByTagName('ml')[0].getElementsByTagName('pathname')[0]))
                pdf_pathname = join(self.path_unpacked, name.split('.')[0], xml_to_text(jurnal_item.getElementsByTagName('web-pdf')[0].getElementsByTagName('pathname')[0]))
                self.found_articles.append(dict(xml=xml_pathname, pdf=pdf_pathname))
            # Print stuff
            sys.stdout.write(p_bar.next())
            sys.stdout.flush()

    ## There should be way to change that but all the other things I've tried
    ## failed :(
    def _add_to_a(self, key, val):
        self.a[key] += val

    def run(self):
        self.connect()
        self._get_file_listing('.ready')
        self._read_file_listing()
        self._get_packages()
        self._download_tars()
        self._check_md5()
        self._extract_packages()
        self._get_metadata_and_fulltex_dir()
        print self.found_articles

    def _progress_bar(self, n):
        num = 0
        while num <= n:
            yield "\r%i%% [%s%s]" % (num/n*100, "="*num, '.'*(n-num))
            num += 1
