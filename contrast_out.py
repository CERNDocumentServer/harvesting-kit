from __future__ import division
from ftplib import FTP
from xml.dom.minidom import parseString
from contrast_out_config import *
from functools import partial
import sys

class ContrastOutConnector(object):
    def __init__(self):
        self.ftp = None
        self.files_list = []
        self.ready_xml = []
        self.a = {}

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
        print >> sys.stdout, "Reading %i files to retrieve packages." % (len(self.files_list))
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
        # Print stuff
        print >> sys.stdout, "\nDone."

    ## There should be way to change that but all the other things I've tried
    ## failed :(
    def _add_to_a(self, key, val):
        self.a[key] += val

    def run(self):
        self.connect()
        self._get_file_listing('.ready')
        self._read_file_listing()

    def _progress_bar(self, n):
        num = 0
        while num <= n:
            yield "\r%i%% %s%s" %(num/n*100,"="*num,'-'*(n-num))
            num += 1
