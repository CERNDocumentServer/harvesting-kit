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

from ftplib import FTP, error_perm
from os.path import join, exists
from os import remove, mkdir, getcwd
from urlparse import urlparse


def create_folders(new_folder):
    """ Creates all the missing folders in the path new_folder
        requires an absolute path. """
    if not exists(new_folder):
        folders = new_folder.split("/")
        folder = "/"
        for i in range(1, len(folders)):
            folder = join(folder, folders[i]).strip()
            if not exists(folder):
                mkdir(folder)


class FtpDownloader(object):
    """ This class provides an interface to easilly connect to an ftp server,
        list its contents and download files/folders.

        @param server: the url to access the ftp server.
        @type server: string
        @param username: the username used to connect to the server.
        @type username: string
        @param passwd: the password used to connect to the server.
        @type passwd: string
        """
    def __init__(self, server, username, passwd):
        server = urlparse(server)
        if server.netloc:
            server = server.netloc
        elif server.path:
            server = server.path
        self._ftp = FTP(server)
        self._username = username
        self._passwd = passwd
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
            FtpDownloader.download_folder() will download all the files
            from the server in the working directory.

            @param folder: the absolute path for the folder on the server.

            @type folder: string
            @param target_folder: absolute or relative path for the
                                  destination folder default is the
                                  working directory.
            @type target_folder: string
            """
        files, folders = self.ls(folder)
        for fl in files:
            self.download(join(folder, fl), target_folder)
        for fld in folders:
            self.download_folder(join(folder, fld), target_folder)

    def download(self, source_file, target_folder=''):
        """ Downloads a file from the ftp server to target folder

        @param source_file: the absolute path for the file on the server
                   it can be the one of the files comming from
                   FtpDownloader.dir().
        @type source_file: string
        @param target_folder: relative or absolute path of the
                              destination folder default is the
                              working directory.
        @type target_folder: string
        """
        if not target_folder.startswith('/'):  # relative path
            target_folder = join(getcwd(), target_folder)
        folder = '/'.join(source_file.split('/')[:-1])
        self.cd(folder)
        destination = join(target_folder, source_file)
        source_file = source_file.split('/')[-1]
        create_folders('/'.join(destination.split('/')[:-1]))
        if not exists(destination):
            try:
                with open(destination, 'wb') as result:
                    self._ftp.retrbinary('RETR %s' % (source_file,), result.write)
            except error_perm as e:  # source_file is a folder
                print e
                remove(join(target_folder, source_file))
        self._ftp.cwd(self._home)

    def cd(self, folder):
        """ Changes the working directory on the server.

            @param folder: the desired directory.
            @type folder: string
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

            @param folder: the folder to be listed.
            @type folder: string

            @returns: a tuple with the list of files in the folder
                      and the list of subfolders in the folder.
            """
        self.cd(folder)
        contents = []
        self._ftp.retrlines('LIST', lambda a: contents.append(a))
        files = filter(lambda a: a.split()[0].startswith('-'), contents)
        folders = filter(lambda a: a.split()[0].startswith('d'), contents)
        files = map(lambda a: ' '.join(a.split()[8:]), files)
        folders = map(lambda a: ' '.join(a.split()[8:]), folders)
        self._ftp.cwd(self._home)
        return files, folders

    def dir(self, folder='', prefix=''):
        """ Lists all the files on the folder given as parameter.
            FtpDownloader.dir() lists all the files on the server.

            @para folder: the folder to be listed.
            @type folder: string

            @param prefix: it does not belong to the interface,
                           it is used to recursively list the subfolders.

            @returns: a list with all the files in the server.
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
