from django.core.files import File
from django.core.files.uploadhandler import TemporaryFileUploadHandler

import re
import zipfile
import os

from pyaxmlparser import APK
import biplist


class InvalidPackage(Exception):
    pass

def search_string(pattern, strings):
    """
    Return the first string that full-matches the pattern.

    :param re.Pattern pattern: Pattern used
    :param iterable strings: Container of strings
    :rparam str or None: string that matches the pattern. None if none
    found.
    """

    for string in strings:
        if pattern.fullmatch(string):
            return string

    return None

class ParsedPackage:
    """
    Analyze and extract the information of a software package.

    Usually, software packages are exported as compressed files using a
    concrete directory structure that is described by the software vendor.
    This class try to extract the data contained in the package considering
    different supported formats.
    """

    IOS_INFO_FILE = "Info.plist"
    IOS_VALID_BUNDLE = "APPL"

    def __init__(self, package_file):
        """
        Extract the data from an initial package file.

        :param django.core.files.File package_file
        """
        self.parse_package(package_file)
        
    def __str__(self):

        if self.valid_parse:
            string = "The package couldn't be parsed"
            
        string = f"Type: {self.type}\n"
        string += f"App name: {self.app_name}\n"
        string += f"OS name: {self.os_name}\n"
        string += f"Icon filename: {self.icon_filename}\n"
        string += f"Version: {self.version}\n"
        return string

    def parse_android(self):
        """
        Extract information from an Android package.
        """

        pack_info = APK(self.package_file)

        if pack_info.is_valid_APK():

            self.metadata = pack_info
            self.type = "APK"
            self.app_name = pack_info.get_app_name()
            self.icon_filename = pack_info.get_app_icon()
            self.os_name = "Android"
            self.version = pack_info.get_androidversion_name()

            self.valid_parse = True

    def parse_ios(self):
        """
        Extract information from an iOS package.
        """

        info_filename = None

        # Search for the information file of the IPA format
        # and process the data that required the zip open
        with zipfile.ZipFile(self.package_file, 'r') as zip_package:
            pattern = re.compile(f".*/?{self.IOS_INFO_FILE}")
                
            # Look for the package information file
            info_filename = search_string(pattern, zip_package.namelist())

            if not info_filename:
                raise InvalidPackage("The package is not supported.")

            info_file = zip_package.open(info_filename)
            plist = biplist.readPlist(info_file)
                
            if (plist["CFBundlePackageType"]
                and plist["CFBundlePackageType"] != self.IOS_VALID_BUNDLE):
                raise InvalidPackage("The package is not supported.")

            # The plist only returns the icon name, not its full path
            icon_name = plist["CFBundleIconFiles"][0]
            pattern = re.compile(f".*/?{icon_name}")
            self.icon_filename = search_string(pattern, zip_package.namelist())

        self.metadata = plist
        self.type = "IPA"
        self.app_name = plist["CFBundleDisplayName"]
        self.os_name = plist["CFBundleSupportedPlatforms"][0]
        self.version = plist["CFBundleInfoDictionaryVersion"]

        self.valid_parse = True
    
    def parse_package(self, package_file):
        """
        Get the data contained in the package file.
        """

        PARSERS = iter([
            self.parse_android,
            self.parse_ios
        ])        

        self.valid_parse = False
        self.zip_package = None
        self.zip_icon_file = None
        self.icon_file = None

        if not package_file:
            raise FileNotFoundError("A file must be provided to create a package object.")

        """
        if not zipfile.is_zipfile(package_file):
            raise InvalidPackage("The package is not a ZIP file.")
        """
        self.package_file = package_file

        while not self.valid_parse:
            parse_function = next(PARSERS)
            parse_function()

    def _open_zip(self):
        """Open the package as a zip file."""
        if not self.zip_package:
            self.zip_package = zipfile.ZipFile(self.package_file)

    def _close_zip(self):
        """Close the package zip file."""
        self._close_icon()

        if self.zip_package:
            self.zip_package.close()
            self.zip_package = None

    def _open_icon(self):
        """Open the package icon file."""
        if self.icon_filename and not self.icon_file:
            self._open_zip()
            self.zip_icon_file = self.zip_package.open(self.icon_filename)

    def _close_icon(self):
        """Close the package icon file."""
        if self.zip_icon_file:
            self.zip_icon_file.close()
            self.zip_icon_file = None

        if self.icon_file:
            self.icon_file.close()
            self.icon_file = None

    def close(self):
        """Close both the icon file and the zip package file."""
        self._close_icon()
        self._close_zip()

    def get_icon(self):
        """Return the icon file as a django File if it exists."""
        
        self._open_icon()
        if self.icon_filename and not self.icon_file:
            self.icon_file = File(self.zip_icon_file)
        return self.icon_file

    @property
    def package_name(self):
        """Return the package file name."""
        if not isinstance(self.package_file, str):
            return self.package_file.name
        else:
            return os.path.basename(self.package_file)

    @property
    def size(self):
        """Return the package size"""
        if not isinstance(self.package_file, str):
            return self.package_file.size
        else:
            return os.path.getsize(self.package_file)

    @property
    def file(self):
        if not isinstance(self.package_file, str):
            return self.package_file
        else:
            return File(open(self.package_file, "rb"))
            

    def to_dict(self):
        """
        Return a dict-like object with the attributes whose value
        is defined.
        """

        d = {
            'name': self.package_name,
            'last_version': self.version,
            'size': self.size,
            'package_type': self.type,
        }

        if self.icon_filename:    
            d['icon_filename'] = self.icon_filename
        
        if self.os_name:
            d['os_name'] = self.os_name

        return d
