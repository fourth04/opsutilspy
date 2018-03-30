# self._ftp.py
"""
File: self._ftp.py
Description: this script is used to make some self._ftp operations more convenient
             add upload and download operations  20111210 version0.1
"""

import ftplib
import os
import socket
import sys

CONST_BUFFER_SIZE = 8192

COLOR_NONE = "\033[m"
COLOR_GREEN = "\033[01;32m"
COLOR_RED = "\033[01;31m"
COLOR_YELLOW = "\033[01;33m"


class FTPClient(object):
    """Docstring for FTPClient. """

    def __init__(self, host, user, passwd):
        """TODO: to be defined1.

        :host: TODO
        :user: TODO
        :passwd: TODO

        """
        self._host = host
        self._user = user
        self._passwd = passwd

    def connect(self):
        try:
            self._ftp = ftplib.FTP(self._host)
            self._ftp.login(self._user, self._passwd)

        except (socket.error, socket.gaierror) as e:
            print(
                "ftp is unavailable,please check the host,username and password!"
            )
            return e

    def disconnect(self):
        self._ftp.quit()

    def upload(self, filename, src_filepath):
        f = open(src_filepath, "rb")
        try:
            self._ftp.storbinary('STOR %s' % filename, f, CONST_BUFFER_SIZE)
        except ftplib.error_perm:
            return False

        return True

    def download(self, filename, dst_filepath):
        f = open(dst_filepath, "wb")
        f_callback = f.write
        try:
            self._ftp.retrbinary("RETR %s" % filename, f_callback,
                                 CONST_BUFFER_SIZE)
        except ftplib.error_perm:
            return False

        return True

    def get_binary(self, filename):
        rv = b""

        def rv_callback(x):
            nonlocal rv
            rv += x

        try:
            self._ftp.retrbinary("RETR %s" % filename, rv_callback,
                                 CONST_BUFFER_SIZE)
        except ftplib.error_perm:
            return b""

        return rv

    def ndir(self):
        self._ftp.dir()

    def nlst(self):
        return self._ftp.nlst()

    def find(self, filename):
        ftp_f_list = self._ftp.nlst()

        if filename in ftp_f_list:
            return True
        else:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.disconnect()
