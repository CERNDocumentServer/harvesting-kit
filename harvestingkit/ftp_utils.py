# -*- coding: utf-8 -*-
##
## This file is part of Harvesting Kit.
## Copyright (C) 2014 CERN.
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
import os
import time

from ftplib import FTP, error_perm
from os.path import join
from os import remove, getcwd
from urlparse import urlparse
from netrc import netrc
from datetime import datetime


class FtpHandler(object):
    """ This class provides an interface to easily connect to an FTP server,
    list its contents and download files/folders.

    :param server: the URL to access the FTP server.
    :type server: string
    :param username: the user-name used to connect to the server.
    :type username: string
    :param passwd: the password used to connect to the server.
    :type passwd: string
    :param netrc_file: path to a netrc file that can be used
                               for authentication with the server.
    :type netrc_file: string
    """
    def __init__(self, server, username='', passwd='', netrc_file=''):
        server = urlparse(server)
        if server.netloc:
            server = server.netloc
        elif server.path:
            server = server.path
        self._ftp = FTP(server)
        self._username = username
        self._passwd = passwd
        if netrc_file:
            logininfo = netrc(netrc_file).authenticators(server)
            self._username, _, self._passwd = logininfo
        self.connect()
        self._home = self._ftp.pwd()

    def connect(self):
        """ Connects and logins to the server. """
        self._ftp.connect()
        self._ftp.login(user=self._username, passwd=self._passwd)

    def close(self):
        """ Closes the connection to the server. """
        self._ftp.close()

    def download_folder(self, folder='', target_folder=''):
        """ Downloads a whole folder from the server.
        FtpHandler.download_folder() will download all the files
        from the server in the working directory.

        :param folder: the absolute path for the folder on the server.

        :type folder: string
        :param target_folder: absolute or relative path for the
                              destination folder default is the
                              working directory.
        :type target_folder: string
        """
        files, folders = self.ls(folder)
        for fl in files:
            self.download(join(folder, fl), target_folder)
        for fld in folders:
            self.download_folder(join(folder, fld), target_folder)

    def download(self, source_file, target_folder=''):
        """ Downloads a file from the FTP server to target folder

        :param source_file: the absolute path for the file on the server
                   it can be the one of the files coming from
                   FtpHandler.dir().
        :type source_file: string
        :param target_folder: relative or absolute path of the
                              destination folder default is the
                              working directory.
        :type target_folder: string
        """
        current_folder = self._ftp.pwd()

        if not target_folder.startswith('/'):  # relative path
            target_folder = join(getcwd(), target_folder)

        folder = os.path.dirname(source_file)
        self.cd(folder)

        if folder.startswith("/"):
            folder = folder[1:]

        destination_folder = join(target_folder, folder)
        if not os.path.exists(destination_folder):
            print("Creating folder", destination_folder)
            os.makedirs(destination_folder)

        source_file = os.path.basename(source_file)
        destination = join(destination_folder, source_file)
        try:
            with open(destination, 'wb') as result:
                self._ftp.retrbinary('RETR %s' % (source_file,),
                                     result.write)
        except error_perm as e:  # source_file is a folder
            print(e)
            remove(join(target_folder, source_file))
            raise
        self._ftp.cwd(current_folder)

    def cd(self, folder):
        """ Changes the working directory on the server.

        :param folder: the desired directory.
        :type folder: string
        """
        if folder.startswith('/'):
            self._ftp.cwd(folder)
        else:
            for subfolder in folder.split('/'):
                if subfolder:
                    self._ftp.cwd(subfolder)

    def ls(self, folder=''):
        """ Lists the files and folders of a specific directory
        default is the current working directory.

        :param folder: the folder to be listed.
        :type folder: string

        :returns: a tuple with the list of files in the folder
                  and the list of subfolders in the folder.
        """
        current_folder = self._ftp.pwd()
        self.cd(folder)
        contents = []
        self._ftp.retrlines('LIST', lambda a: contents.append(a))
        files = filter(lambda a: a.split()[0].startswith('-'), contents)
        folders = filter(lambda a: a.split()[0].startswith('d'), contents)
        files = map(lambda a: ' '.join(a.split()[8:]), files)
        folders = map(lambda a: ' '.join(a.split()[8:]), folders)
        self._ftp.cwd(current_folder)
        return files, folders

    def dir(self, folder='', prefix=''):
        """ Lists all the files on the folder given as parameter.
        FtpHandler.dir() lists all the files on the server.

        :para folder: the folder to be listed.
        :type folder: string

        :param prefix: it does not belong to the interface,
                       it is used to recursively list the subfolders.

        :returns: a list with all the files in the server.
        """
        files, folders = self.ls(folder)
        result = files
        inner = []
        for fld in folders:
            try:
                inner += self.dir(folder + '/' + fld, prefix + fld + '/')
            except:
                pass
        result += inner
        if prefix:
            result = map(lambda a: prefix + a, result)
        return result

    def mkdir(self, folder):
        """ Creates a folder in the server

        :param folder: the folder to be created.
        :type folder: string
        """
        current_folder = self._ftp.pwd()
        #creates the necessary folders on
        #the server if they don't exist
        folders = folder.split('/')
        for fld in folders:
            try:
                self.cd(fld)
            except error_perm:  # folder does not exist
                self._ftp.mkd(fld)
                self.cd(fld)
        self.cd(current_folder)

    def rm(self, filename):
        """ Delete a file from the server.

        :param filename: the file to be deleted.
        :type filename: string
        """
        try:
            self._ftp.delete(filename)
        except error_perm:  # target is either a directory
                            # either it does not exist
            try:
                current_folder = self._ftp.pwd()
                self.cd(filename)
            except error_perm:
                print('550 Delete operation failed %s '
                      'does not exist!' % (filename,))
            else:
                self.cd(current_folder)
                print('550 Delete operation failed %s '
                      'is a folder. Use rmdir function '
                      'to delete it.' % (filename,))

    def rmdir(self, foldername):
        """ Delete a folder from the server.

        :param foldername: the folder to be deleted.
        :type foldername: string
        """
        current_folder = self._ftp.pwd()
        try:
            self.cd(foldername)
        except error_perm:
            print('550 Delete operation failed folder %s '
                  'does not exist!' % (foldername,))
        else:
            self.cd(current_folder)
            try:
                self._ftp.rmd(foldername)
            except error_perm:  # folder not empty
                self.cd(foldername)
                contents = self.ls()
                #delete the files
                map(self._ftp.delete, contents[0])
                #delete the subfolders
                map(self.rmdir, contents[1])
                self.cd(current_folder)
                self._ftp.rmd(foldername)

    def get_filesize(self, filename):
        """ Returns the filesize of a file

        :param filename: the full path to the file on the server.
        :type filename: string

        :returns: string representation of the filesize.
        """
        result = []

        def dir_callback(val):
            result.append(val.split()[4])

        self._ftp.dir(filename, dir_callback)
        return result[0]

    def get_datestamp(self, filename):
        datestamp = self._ftp.sendcmd('MDTM ' + filename)
        datestamp = datetime.strptime(datestamp[4:],
                                      "%Y%m%d%H%M%S").strftime("%Y-%M-%d")
        return datestamp

    def check_pkgs_integrity(self, filelist, logger,
                             timeout=120, sleep_time=10):
        """ Checks if files are not being uploaded to server.

        :param filelist - a list of filenames to check.
        :type filelist: list
        :param timeout - time after which the script will register an error.
        :type timeout: int
        """
        ref_1 = []
        ref_2 = []
        i = 1
        print("\nChecking packages integrity.")
        for filename in filelist:
            ref_1.append(self.get_filesize(filename))
        print("\nGoing to sleep for %i sec." % (sleep_time,))
        time.sleep(sleep_time)

        while sleep_time * i < timeout:
            for filename in filelist:
                ref_2.append(self.get_filesize(filename))
            if ref_1 == ref_2:
                print(sys.stdout, "\nIntegrity OK:)")
                logger.info("Packages integrity OK.")
                break
            else:
                print("\nWaiting %d time for integrity..." % (i,))
                logger.info("\nWaiting %d time for integrity..." % (i,))
                i += 1
                ref_1, ref_2 = ref_2, []
                time.sleep(sleep_time)
        else:
            not_finished_files = []
            for count, val1 in enumerate(ref_1):
                if val1 != ref_2[count]:
                    not_finished_files.append(filelist[count])

            print("\nOMG, OMG something wrong with integrity.")
            logger.error("Integrity check failed for files %s"
                         % (not_finished_files,))

    def upload(self, filename, location=''):
        """ Uploads a file on the server to the desired location

        :param filename: the name of the file to be uploaded.
        :type filename: string
        :param location: the directory in which the file will
                         be stored.
        :type location: string
        """
        current_folder = self._ftp.pwd()
        self.mkdir(location)
        self.cd(location)
        fl = open(filename, 'rb')
        filename = filename.split('/')[-1]
        self._ftp.storbinary('STOR %s' % filename, fl)
        fl.close()
        self.cd(current_folder)
