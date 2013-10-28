from ftplib import FTP
from xml.dom.minidom import parseString
from contrast_out_config import *


class ContrastOutConnector(object):
    def __init__(self):
        self.ftp = None
        self.ready_file_list = []
        self.ready_xml = []
        self.a = ''

    def connect(self):
        """Logs into the specified ftp server and returns connector."""
        self.ftp = FTP(CFG_CONTRAST_OUT_URL)
        self.ftp.login(user=CFG_CONTRAST_OUT_LOGIN, passwd=CFG_CONTRAST_OUT_PASSWORD)

    def _get_file_listing(self, phrase=None):
        if phrase:
            self.ready_file_list = filter(lambda x: phrase in x, self.ftp.nlst())
        else:
            self.ready_file_list = self.ftp.nlst()

    def read_ready_list(self):
        for f in self.ready_file_list:
            self.ftp.retrlines('RETR %s' % (f,), self._add_to_a)
        print self.a
            #self.ready_xml.append(parseString(a))

    ## There should be way to change that but all the other things I've tried 
    ## failed :(
    def _add_to_a(self, x):
        self.a += x
