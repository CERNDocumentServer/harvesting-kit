from __future__ import division

import sys

from functools import partial
from ftplib import FTP
from os.path import join
from tempfile import mkdtemp
from xml.dom.minidom import parseString

from scoap3utils import xml_to_text
from contrast_out_config import *
from invenio.config import CFG_TMPSHAREDDIR

class ContrastOutConnector(object):
    def __init__(self):
        self.ftp = None
        self.files_list = []
        self.ready_xml = []
        self.a = {}
        self.retrieved_packages = []

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
        print >> sys.stdout, "\nRetrieving packages."
        # Create progrss bar
        p_bar = self._progress_bar(len(self.files_list))
        # Print stuff
        sys.stdout.write(p_bar.next())
        sys.stdout.flush()

        for pack in self.ready_xml:
            filenames = pack.getElementsByTagName('filename')
            for filename in filenames:
                self.retrieved_packages.append(xml_to_text(filename))
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

        for filename in self.retrieved_packages:
            tar_file = open(join(self.path_tar,filename), 'wb')
            self.ftp.retrbinary('RETR %s' % filename, tar_file.write)
            tar_file.close()
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

    def _progress_bar(self, n):
        num = 0
        while num <= n:
            yield "\r%i%% %s%s" %(num/n*100,"="*num,'-'*(n-num))
            num += 1
