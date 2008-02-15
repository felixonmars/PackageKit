#!/usr/bin/python
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# Copyright (C) 2007
#    Tim Lauridsen <timlau@fedoraproject.org>
#    Seth Vidal <skvidal@fedoraproject.org>
#    Luke Macken <lmacken@redhat.com>
#    James Bowes <jbowes@dangerouslyinc.com>
#    Robin Norwood <rnorwood@redhat.com>

# imports

import re

from packagekit.daemonBackend import PackageKitBaseBackend

# This is common between backends
from packagekit.daemonBackend import PACKAGEKIT_DBUS_INTERFACE, PACKAGEKIT_DBUS_PATH

from packagekit.enums import *
from packagekit.daemonBackend import PackagekitProgress
import yum
from urlgrabber.progress import BaseMeter,format_time,format_number
from yum.rpmtrans import RPMBaseCallback
from yum.constants import *
from yum.update_md import UpdateMetadata
from yum.callbacks import *
from yum.misc import prco_tuple_to_string, unique

import dbus
import dbus.service
import dbus.mainloop.glib

import rpmUtils
import exceptions
import types
import signal
import time
import os.path

# Global vars
yumbase = None
progress = PackagekitProgress()  # Progress object to store the progress

groupMap = {
'desktops;gnome-desktop'                      : GROUP_DESKTOP_GNOME,
'desktops;window-managers'                    : GROUP_DESKTOP_OTHER,
'desktops;kde-desktop'                        : GROUP_DESKTOP_KDE,
'desktops;xfce-desktop'                       : GROUP_DESKTOP_XFCE,
'apps;authoring-and-publishing'               : GROUP_PUBLISHING,
'apps;office'                                 : GROUP_OFFICE,
'apps;sound-and-video'                        : GROUP_MULTIMEDIA,
'apps;editors'                                : GROUP_OFFICE,
'apps;engineering-and-scientific'             : GROUP_OTHER,
'apps;games'                                  : GROUP_GAMES,
'apps;graphics'                               : GROUP_GRAPHICS,
'apps;text-internet'                          : GROUP_INTERNET,
'apps;graphical-internet'                     : GROUP_INTERNET,
'apps;education'                              : GROUP_EDUCATION,
'development;kde-software-development'        : GROUP_PROGRAMMING,
'development;gnome-software-development'      : GROUP_PROGRAMMING,
'development;development-tools'               : GROUP_PROGRAMMING,
'development;eclipse'                         : GROUP_PROGRAMMING,
'development;development-libs'                : GROUP_PROGRAMMING,
'development;x-software-development'          : GROUP_PROGRAMMING,
'development;web-development'                 : GROUP_PROGRAMMING,
'development;legacy-software-development'     : GROUP_PROGRAMMING,
'development;ruby'                            : GROUP_PROGRAMMING,
'development;java-development'                : GROUP_PROGRAMMING,
'development;xfce-software-development'       : GROUP_PROGRAMMING,
'servers;clustering'                          : GROUP_SERVERS,
'servers;dns-server'                          : GROUP_SERVERS,
'servers;server-cfg'                          : GROUP_SERVERS,
'servers;news-server'                         : GROUP_SERVERS,
'servers;web-server'                          : GROUP_SERVERS,
'servers;smb-server'                          : GROUP_SERVERS,
'servers;sql-server'                          : GROUP_SERVERS,
'servers;ftp-server'                          : GROUP_SERVERS,
'servers;printing'                            : GROUP_SERVERS,
'servers;mysql'                               : GROUP_SERVERS,
'servers;mail-server'                         : GROUP_SERVERS,
'servers;network-server'                      : GROUP_SERVERS,
'servers;legacy-network-server'               : GROUP_SERVERS,
'base-system;java'                            : GROUP_SYSTEM,
'base-system;base-x'                          : GROUP_SYSTEM,
'base-system;system-tools'                    : GROUP_ADMIN_TOOLS,
'base-system;fonts'                           : GROUP_FONTS,
'base-system;hardware-support'                : GROUP_SYSTEM,
'base-system;dial-up'                         : GROUP_SYSTEM,
'base-system;admin-tools'                     : GROUP_ADMIN_TOOLS,
'base-system;legacy-software-support'         : GROUP_LEGACY,
'base-system;base'                            : GROUP_SYSTEM,
'base-system;virtualization'                  : GROUP_VIRTUALIZATION,
'base-system;legacy-fonts'                    : GROUP_FONTS,
'language-support;khmer-support'              : GROUP_LOCALIZATION,
'language-support;persian-support'            : GROUP_LOCALIZATION,
'language-support;georgian-support'           : GROUP_LOCALIZATION,
'language-support;malay-support'              : GROUP_LOCALIZATION,
'language-support;tonga-support'              : GROUP_LOCALIZATION,
'language-support;portuguese-support'         : GROUP_LOCALIZATION,
'language-support;japanese-support'           : GROUP_LOCALIZATION,
'language-support;hungarian-support'          : GROUP_LOCALIZATION,
'language-support;somali-support'             : GROUP_LOCALIZATION,
'language-support;punjabi-support'            : GROUP_LOCALIZATION,
'language-support;bhutanese-support'          : GROUP_LOCALIZATION,
'language-support;british-support'            : GROUP_LOCALIZATION,
'language-support;korean-support'             : GROUP_LOCALIZATION,
'language-support;lao-support'                : GROUP_LOCALIZATION,
'language-support;inuktitut-support'          : GROUP_LOCALIZATION,
'language-support;german-support'             : GROUP_LOCALIZATION,
'language-support;hindi-support'              : GROUP_LOCALIZATION,
'language-support;faeroese-support'           : GROUP_LOCALIZATION,
'language-support;swedish-support'            : GROUP_LOCALIZATION,
'language-support;tsonga-support'             : GROUP_LOCALIZATION,
'language-support;russian-support'            : GROUP_LOCALIZATION,
'language-support;serbian-support'            : GROUP_LOCALIZATION,
'language-support;latvian-support'            : GROUP_LOCALIZATION,
'language-support;samoan-support'             : GROUP_LOCALIZATION,
'language-support;sinhala-support'            : GROUP_LOCALIZATION,
'language-support;catalan-support'            : GROUP_LOCALIZATION,
'language-support;lithuanian-support'         : GROUP_LOCALIZATION,
'language-support;turkish-support'            : GROUP_LOCALIZATION,
'language-support;arabic-support'             : GROUP_LOCALIZATION,
'language-support;vietnamese-support'         : GROUP_LOCALIZATION,
'language-support;mongolian-support'          : GROUP_LOCALIZATION,
'language-support;tswana-support'             : GROUP_LOCALIZATION,
'language-support;irish-support'              : GROUP_LOCALIZATION,
'language-support;italian-support'            : GROUP_LOCALIZATION,
'language-support;slovak-support'             : GROUP_LOCALIZATION,
'language-support;slovenian-support'          : GROUP_LOCALIZATION,
'language-support;belarusian-support'         : GROUP_LOCALIZATION,
'language-support;northern-sotho-support'     : GROUP_LOCALIZATION,
'language-support;kannada-support'            : GROUP_LOCALIZATION,
'language-support;malayalam-support'          : GROUP_LOCALIZATION,
'language-support;swati-support'              : GROUP_LOCALIZATION,
'language-support;breton-support'             : GROUP_LOCALIZATION,
'language-support;romanian-support'           : GROUP_LOCALIZATION,
'language-support;greek-support'              : GROUP_LOCALIZATION,
'language-support;tagalog-support'            : GROUP_LOCALIZATION,
'language-support;zulu-support'               : GROUP_LOCALIZATION,
'language-support;tibetan-support'            : GROUP_LOCALIZATION,
'language-support;danish-support'             : GROUP_LOCALIZATION,
'language-support;afrikaans-support'          : GROUP_LOCALIZATION,
'language-support;southern-sotho-support'     : GROUP_LOCALIZATION,
'language-support;bosnian-support'            : GROUP_LOCALIZATION,
'language-support;brazilian-support'          : GROUP_LOCALIZATION,
'language-support;basque-support'             : GROUP_LOCALIZATION,
'language-support;welsh-support'              : GROUP_LOCALIZATION,
'language-support;thai-support'               : GROUP_LOCALIZATION,
'language-support;telugu-support'             : GROUP_LOCALIZATION,
'language-support;low-saxon-support'          : GROUP_LOCALIZATION,
'language-support;urdu-support'               : GROUP_LOCALIZATION,
'language-support;tamil-support'              : GROUP_LOCALIZATION,
'language-support;indonesian-support'         : GROUP_LOCALIZATION,
'language-support;gujarati-support'           : GROUP_LOCALIZATION,
'language-support;xhosa-support'              : GROUP_LOCALIZATION,
'language-support;chinese-support'            : GROUP_LOCALIZATION,
'language-support;czech-support'              : GROUP_LOCALIZATION,
'language-support;venda-support'              : GROUP_LOCALIZATION,
'language-support;bulgarian-support'          : GROUP_LOCALIZATION,
'language-support;albanian-support'           : GROUP_LOCALIZATION,
'language-support;galician-support'           : GROUP_LOCALIZATION,
'language-support;armenian-support'           : GROUP_LOCALIZATION,
'language-support;dutch-support'              : GROUP_LOCALIZATION,
'language-support;oriya-support'              : GROUP_LOCALIZATION,
'language-support;maori-support'              : GROUP_LOCALIZATION,
'language-support;nepali-support'             : GROUP_LOCALIZATION,
'language-support;icelandic-support'          : GROUP_LOCALIZATION,
'language-support;ukrainian-support'          : GROUP_LOCALIZATION,
'language-support;assamese-support'           : GROUP_LOCALIZATION,
'language-support;bengali-support'            : GROUP_LOCALIZATION,
'language-support;spanish-support'            : GROUP_LOCALIZATION,
'language-support;hebrew-support'             : GROUP_LOCALIZATION,
'language-support;estonian-support'           : GROUP_LOCALIZATION,
'language-support;french-support'             : GROUP_LOCALIZATION,
'language-support;croatian-support'           : GROUP_LOCALIZATION,
'language-support;filipino-support'           : GROUP_LOCALIZATION,
'language-support;finnish-support'            : GROUP_LOCALIZATION,
'language-support;norwegian-support'          : GROUP_LOCALIZATION,
'language-support;southern-ndebele-support'   : GROUP_LOCALIZATION,
'language-support;polish-support'             : GROUP_LOCALIZATION,
'language-support;gaelic-support'             : GROUP_LOCALIZATION,
'language-support;marathi-support'            : GROUP_LOCALIZATION,
'language-support;ethiopic-support'           : GROUP_LOCALIZATION
}

MetaDataMap = {
'repomd.xml'             : "repository",
'primary.sqlite.bz2'     : "package",
'primary.xml.gz'         : "package",
'filelists.sqlite.bz2'   : "filelist",
'filelists.xml.gz'       : "filelist",
'other.sqlite.bz2'       : "changelog",
'other.xml.gz'           : "changelog",
'comps.xml'              : "group",
'updateinfo.xml.gz'      : "update"
}

GUI_KEYS = re.compile(r'(qt)|(gtk)')

class GPGKeyNotImported(exceptions.Exception):
    pass

def sigquit(signum, frame):
    print >> sys.stderr, "Quit signal sent - exiting immediately"
    if yumbase:
        print >> sys.stderr, "unlocking Yum"
        yumbase.closeRpmDB()
        yumbase.doUnlock(YUM_PID_FILE)
    sys.exit(1)

# This is specific to this backend
PACKAGEKIT_DBUS_SERVICE = 'org.freedesktop.PackageKitYumBackend'

class PackageKitYumBackend(PackageKitBaseBackend):

    # Packages there require a reboot
    rebootpkgs = ("kernel", "kernel-smp", "kernel-xen-hypervisor", "kernel-PAE",
              "kernel-xen0", "kernel-xenU", "kernel-xen", "kernel-xen-guest",
              "glibc", "hal", "dbus", "xen")

    def __init__(self, bus_name, dbus_path):
        signal.signal(signal.SIGQUIT, sigquit)


        PackageKitBaseBackend.__init__(self,
                                       bus_name,
                                       dbus_path)
        print "__init__"

#
# Signals ( backend -> engine -> client )
#

    #FIXME: _show_description and _show_package wrap Description and
    #       Package so that the encoding can be fixed. This is ugly.
    #       we could probably use a decorator to do it instead.

    def _show_package(self,pkg,status):
        '''
        send 'package' signal
        @param info: the enumerated INFO_* string
        @param id: The package ID name, e.g. openoffice-clipart;2.6.22;ppc64;fedora
        @param summary: The package Summary
        convert the summary to UTF before sending
        '''
        id = self._pkg_to_id(pkg)
        summary = self._toUTF(pkg.summary)
        self.Package(status,id,summary)

    def _show_description(self,id,license,group,desc,url,bytes):
        '''
        Send 'description' signal
        @param id: The package ID name, e.g. openoffice-clipart;2.6.22;ppc64;fedora
        @param license: The license of the package
        @param group: The enumerated group
        @param desc: The multi line package description
        @param url: The upstream project homepage
        @param bytes: The size of the package, in bytes
        convert the description to UTF before sending
        '''
        desc = self._toUTF(desc)
        self.Description(id,license,group,desc,url,bytes)

#
# Utility methods for Signals
#

    def _toUTF( self, txt ):
        rc=""
        if isinstance(txt,types.UnicodeType):
            return txt
        else:
            try:
                rc = unicode( txt, 'utf-8' )
            except UnicodeDecodeError, e:
                rc = unicode( txt, 'iso-8859-1' )
            return rc

    def _pkg_to_id(self,pkg):
        pkgver = self._get_package_ver(pkg)
        id = self._get_package_id(pkg.name, pkgver, pkg.arch, pkg.repo)
        return id

#
# Methods ( client -> engine -> backend )
#

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def Init(self):
        self.yumbase = PackageKitYumBase()
        yumbase = self.yumbase
        self._setup_yum()
        self.doLock()

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def Exit(self):
        if self.isLocked():
            self.doUnlock()

        self.loop.quit()

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def Lock(self):
        self.doLock()

    def doLock(self):
        ''' Lock Yum'''
        retries = 0
        while not self.isLocked():
            try: # Try to lock yum
                self.yumbase.doLock( YUM_PID_FILE )
                PackageKitBaseBackend.doLock(self)
            except:
                if retries == 0:
                    self.StatusChanged(STATUS_WAIT)
                time.sleep(2)
                retries += 1
                if retries > 100:
                    self.ErrorCode(ERROR_INTERNAL_ERROR,'Yum is locked by another application')
                    self.Exit()

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def Unlock(self):
        self.doUnlock()

    def doUnlock(self):
        ''' Unlock Yum'''
        if self.isLocked():
            PackageKitBaseBackend.doUnlock(self)
            self.yumbase.closeRpmDB()
            self.yumbase.doUnlock(YUM_PID_FILE)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def SearchName(self, filters, search):
        '''
        Implement the {backend}-search-name functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()

        searchlist = ['name']
        self.StatusChanged(STATUS_QUERY)

        self._do_search(searchlist, filters, search)
        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def SearchDetails(self,filters,key):
        '''
        Implement the {backend}-search-details functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()

        searchlist = ['name', 'summary', 'description', 'group']
        self.StatusChanged(STATUS_QUERY)
        self._do_search(searchlist, filters, key)
        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def SearchGroup(self,filters,key):
        '''
        Implement the {backend}-search-group functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.yumbase.conf.cache = 1 # Only look in cache.
        self.StatusChanged(STATUS_QUERY)

        try:
            pkgGroupDict = self._buildGroupDict()
            self.yumbase.conf.cache = 1 # Only look in cache.
            fltlist = filters.split(';')
            found = {}

            if not FILTER_NOT_INSTALLED in fltlist:
                # Check installed for group
                for pkg in self.yumbase.rpmdb:
                    group = GROUP_OTHER                    # Default Group
                    if pkgGroupDict.has_key(pkg.name):     # check if pkg name exist in package / group dictinary
                        cg = pkgGroupDict[pkg.name]
                        if groupMap.has_key(cg):
                            group = groupMap[cg]           # use the pk group name, instead of yum 'category/group'
                    if group == key:
                        if self._do_extra_filtering(pkg, fltlist):
                            self._show_package(pkg, INFO_INSTALLED)
            if not FILTER_INSTALLED in fltlist:
                # Check available for group
                for pkg in self.yumbase.pkgSack:
                    group = GROUP_OTHER
                    if pkgGroupDict.has_key(pkg.name):
                        cg = pkgGroupDict[pkg.name]
                        if groupMap.has_key(cg):
                            group = groupMap[cg]
                    if group == key:
                        if self._do_extra_filtering(pkg, fltlist):
                            self._show_package(pkg, INFO_AVAILABLE)
        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def SearchFile(self,filters,key):
        '''
        Implement the {backend}-search-file functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_QUERY)

        #self.yumbase.conf.cache = 1 # Only look in cache.
        fltlist = filters.split(';')
        found = {}
        if not FILTER_NOT_INSTALLED in fltlist:
            # Check installed for file
            matches = self.yumbase.rpmdb.searchFiles(key)
            for pkg in matches:
                if not found.has_key(str(pkg)):
                    if self._do_extra_filtering(pkg, fltlist):
                        self._show_package(pkg, INFO_INSTALLED)
                        found[str(pkg)] = 1
        if not FILTER_INSTALLED in fltlist:
            # Check available for file
            self.yumbase.repos.populateSack(mdtype='filelists')
            matches = self.yumbase.pkgSack.searchFiles(key)
            for pkg in matches:
                if found.has_key(str(pkg)):
                    if self._do_extra_filtering(pkg, fltlist):
                        self._show_package(pkg, INFO_AVAILABLE)
                        found[str(pkg)] = 1

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='sb', out_signature='')
    def GetRequires(self,package,recursive):
        '''
        Print a list of requires for a given package
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_INFO)
        pkg,inst = self._findPackage(package)
        pkgs = self.yumbase.rpmdb.searchRequires(pkg.name)
        for pkg in pkgs:
            if inst:
                self._show_package(pkg,INFO_INSTALLED)
            else:
                self._show_package(pkg,INFO_AVAILABLE)

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='sb', out_signature='')
    def GetDepends(self,package,recursive):
        '''
        Print a list of depends for a given package
        '''
        self.AllowCancel(True)
        self.PercentageChanged(0)
        self.StatusChanged(STATUS_INFO)

        name = package.split(';')[0]
        pkg,inst = self._findPackage(package)
        results = {}
        if pkg:
            deps = self._get_best_dependencies(pkg)
        else:
            self.ErrorCode(ERROR_PACKAGE_NOT_FOUND,'Package was not found')
            self.Exit()
        for pkg in deps:
            if pkg.name != name:
                pkgver = self._get_package_ver(pkg)
                id = self._get_package_id(pkg.name, pkgver, pkg.arch, pkg.repoid)

                if self._is_inst(pkg):
                    self._show_package(pkg, INFO_INSTALLED)
                else:
                    if self._installable(pkg):
                        self._show_package(pkg, INFO_AVAILABLE)

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def UpdateSystem(self):
        '''
        Implement the {backend}-update-system functionality
        '''
        self.AllowCancel(False)
        self.PercentageChanged(0)

        txmbr = self.yumbase.update() # Add all updates to Transaction
        if txmbr:
            self._runYumTransaction()
        else:
            self.ErrorCode(ERROR_INTERNAL_ERROR,"Nothing to do")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def RefreshCache(self):
        '''
        Implement the {backend}-refresh_cache functionality
        '''
        self.AllowCancel(True);
        self.PercentageChanged(0)
        self.StatusChanged(STATUS_REFRESH_CACHE)

        pct = 0
        try:
            if len(self.yumbase.repos.listEnabled()) == 0:
                self.PercentageChanged(100)
                self.Finished(EXIT_SUCCESS)
                return

            #work out the slice for each one
            bump = (95/len(self.yumbase.repos.listEnabled()))/2

            for repo in self.yumbase.repos.listEnabled():
                repo.metadata_expire = 0
                self.yumbase.repos.populateSack(which=[repo.id], mdtype='metadata', cacheonly=1)
                pct+=bump
                self.PercentageChanged(pct)
                self.yumbase.repos.populateSack(which=[repo.id], mdtype='filelists', cacheonly=1)
                pct+=bump
                self.PercentageChanged(pct)

            self.PercentageChanged(95)
            # Setup categories/groups
            self.yumbase.doGroupSetup()
            #we might have a rounding error
            self.PercentageChanged(100)

        except yum.Errors.YumBaseError, e:
            self.ErrorCode(ERROR_INTERNAL_ERROR,str(e))
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def Resolve(self, filters, name):
        '''
        Implement the {backend}-resolve functionality
        '''
        self.AllowCancel(True);
        self.NoPercentageUpdates()
        self.yumbase.conf.cache = 1 # Only look in cache.
        self.StatusChanged(STATUS_QUERY)

        fltlist = filters.split(';')
        try:
            # Get installed packages
            installedByKey = self.yumbase.rpmdb.searchNevra(name=name)
            if FILTER_NOT_INSTALLED not in fltlist:
                for pkg in installedByKey:
                    self._show_package(pkg,INFO_INSTALLED)
            # Get available packages
            if FILTER_INSTALLED not in fltlist:
                for pkg in self.yumbase.pkgSack.returnNewestByNameArch():
                    if pkg.name == name:
                        show = True
                        for instpo in installedByKey:
                            # Check if package have a smaller & equal EVR to a inst pkg
                            if pkg.EVR < instpo.EVR or pkg.EVR == instpo.EVR:
                                show = False
                        if show:
                            self._show_package(pkg,INFO_AVAILABLE)
                            break
        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def InstallPackage(self, package):
        '''
        Implement the {backend}-install functionality
        This will only work with yum 3.2.4 or higher
        '''
        self.AllowCancel(False)
        self.PercentageChanged(0)

        pkg,inst = self._findPackage(package)
        if pkg:
            if inst:
                self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,'Package already installed')
                self.Exit()
            try:
                txmbr = self.yumbase.install(name=pkg.name)
                self._runYumTransaction()
            except yum.Errors.InstallError,e:
                msgs = ';'.join(e)
                self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,msgs)
                self.Exit()
        else:
            self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,"Package was not found")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def InstallFile (self, inst_file):
        '''
        Implement the {backend}-install_file functionality
        Install the package containing the inst_file file
        Needed to be implemented in a sub class
        '''
        self.AllowCancel(False);
        self.PercentageChanged(0)

        pkgs_to_inst = []
        self.yumbase.conf.gpgcheck=0
        self._localInstall(inst_file)
        try:
            # Added the package to the transaction set
            if len(self.yumbase.tsInfo) > 0:
                self._runYumTransaction()
        except yum.Errors.InstallError,e:
            msgs = ';'.join(e)
            self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,msgs)
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def UpdatePackage(self, package):
        '''
        Implement the {backend}-update functionality
        This will only work with yum 3.2.4 or higher
        '''
        self.AllowCancel(False);
        self.PercentageChanged(0)

        pkg,inst = self._findPackage(package)
        if pkg:
            txmbr = self.yumbase.update(name=pkg.name)
            if txmbr:
                self._runYumTransaction()
            else:
                self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,"No available updates")
                self.Exit()
        else:
            self.ErrorCode(ERROR_PACKAGE_ALREADY_INSTALLED,"No available updates")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='sb', out_signature='')
    def RemovePackage(self, package, allowdep):
        '''
        Implement the {backend}-remove functionality
        '''
        self.AllowCancel(False);
        self.PercentageChanged(0)

        pkg,inst = self._findPackage( package)
        if pkg and inst:
            txmbr = self.yumbase.remove(name=pkg.name)
            if txmbr:
                if allowdep:
                    self._runYumTransaction(removedeps=True)
                else:
                    self._runYumTransaction(removedeps=False)
            else:
                self.ErrorCode(ERROR_PACKAGE_NOT_INSTALLED,"Package is not installed")
                self.Exit()
        else:
            self.ErrorCode(ERROR_PACKAGE_NOT_INSTALLED,"Package is not installed")
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def GetDescription(self, package):
        '''
        Print a detailed description for a given package
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_INFO)

        pkg,inst = self._findPackage(package)
        if pkg:
            self._show_package_description(pkg)            
        else:
            self.ErrorCode(ERROR_INTERNAL_ERROR,'Package was not found')
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def GetFiles(self, package):
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_INFO)

        pkg,inst = self._findPackage(package)
        if pkg:
            files = pkg.returnFileEntries('dir')
            files.extend(pkg.returnFileEntries()) # regular files

            file_list = ";".join(files)

            self.Files(package, file_list)
        else:
            self.ErrorCode(ERROR_INTERNAL_ERROR,'Package was not found')
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def GetUpdates(self):
        '''
        Implement the {backend}-get-updates functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_INFO)
        try:
            ygl = self.yumbase.doPackageLists(pkgnarrow='updates')
            md = self.updateMetadata
            for pkg in ygl.updates:
                # Get info about package in updates info
                notice = md.get_notice((pkg.name, pkg.version, pkg.release))
                if notice:
                    status = self._get_status(notice)
                    self._show_package(pkg,status)
                else:
                    self._show_package(pkg,INFO_NORMAL)
        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

        self.Finished(EXIT_SUCCESS)
        
    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='ss', out_signature='')
    def GetPackages(self,filters,showdesc='no'):
        '''
        Search for yum packages
        @param searchlist: The yum package fields to search in
        @param filters: package types to search (all,installed,available)
        @param key: key to seach for
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.yumbase.conf.cache = 1 # Only look in cache.
        self.StatusChanged(STATUS_QUERY)

        showDesc = (showdesc == 'yes' or showdesc == 'only' )
        showPkg = (showdesc != 'only')
        print showDesc,showPkg
        try:
            fltlist = filters.split(';')
            available = []
            count = 1
            if FILTER_NOT_INSTALLED not in fltlist:
                for pkg in self.yumbase.rpmdb:
                    if self._do_extra_filtering(pkg,fltlist):
                        if showPkg:
                            self._show_package(pkg, INFO_INSTALLED)
                        if showDesc:
                            self._show_package_description(pkg)
                        

        # Now show available packages.
            if FILTER_INSTALLED not in fltlist:
                for pkg in self.yumbase.pkgSack.returnNewestByNameArch():
                    if self._do_extra_filtering(pkg,fltlist):
                        if showPkg:
                            self._show_package(pkg, INFO_AVAILABLE)
                        if showDesc:
                            self._show_package_description(pkg)
        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

        self.Finished(EXIT_SUCCESS)
        

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='sb', out_signature='')
    def RepoEnable(self, repoid, enable):
        '''
        Implement the {backend}-repo-enable functionality
        '''
        try:
            repo = self.yumbase.repos.getRepo(repoid)
            if enable:
                if not repo.isEnabled():
                    repo.enablePersistent()
            else:
                if repo.isEnabled():
                    repo.disablePersistent()

        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_REPO_NOT_FOUND, "repo %s is not found" % repoid)
            self.Exit()

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='', out_signature='')
    def GetRepoList(self):
        '''
        Implement the {backend}-get-repo-list functionality
        '''
        self.StatusChanged(STATUS_INFO)
        for repo in self.yumbase.repos.repos.values():
            if repo.isEnabled():
                self.RepoDetail(repo.id,repo.name,True)
            else:
                self.RepoDetail(repo.id,repo.name,False)

        self.Finished(EXIT_SUCCESS)


    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='s', out_signature='')
    def GetUpdateDetail(self,package):
        '''
        Implement the {backend}-get-update_detail functionality
        '''
        self.AllowCancel(True)
        self.NoPercentageUpdates()
        self.StatusChanged(STATUS_INFO)
        pkg,inst = self._findPackage(package)
        update = self._get_updated(pkg)
        obsolete = self._get_obsoleted(pkg.name)
        desc,urls,reboot = self._get_update_extras(pkg)
        cve_url = self._format_list(urls['cve'])
        bz_url = self._format_list(urls['bugzilla'])
        vendor_url = self._format_list(urls['vendor'])

        self.UpdateDetail(package,update,obsolete,vendor_url,bz_url,cve_url,reboot,desc)

        self.Finished(EXIT_SUCCESS)

    @dbus.service.method(PACKAGEKIT_DBUS_INTERFACE,
                         in_signature='sss', out_signature='')
    def RepoSetData(self, repoid, parameter, value):
        '''
        Implement the {backend}-repo-set-data functionality
        '''
        self.AllowCancel(False)
        self.NoPercentageUpdates()
        # Get the repo
        repo = self.yumbase.repos.getRepo(repoid)
        if repo:
            repo.cfg.set(repoid, parameter, value)
            try:
                repo.cfg.write(file(repo.repofile, 'w'))
            except IOError, e:
                self.ErrorCode(ERROR_INTERNAL_ERROR,str(e))
                self.Exit()
        else:
            self.ErrorCode(ERROR_REPO_NOT_FOUND,'repo %s not found' % repoid)
            self.Exit()

        self.Finished(EXIT_SUCCESS)

#
# Utility methods for Methods
#

    def _do_search(self,searchlist,filters,key):
        '''
        Search for yum packages
        @param searchlist: The yum package fields to search in
        @param filters: package types to search (all,installed,available)
        @param key: key to seach for
        '''
        self.yumbase.conf.cache = 1 # Only look in cache.
        try:
            res = self.yumbase.searchGenerator(searchlist, [key])
            fltlist = filters.split(';')

            available = []
            count = 1
            for (pkg,values) in res:
                # are we installed?
                if pkg.repo.id == 'installed':
                    if FILTER_NOT_INSTALLED not in fltlist:
                        if self._do_extra_filtering(pkg,fltlist):
                            count+=1
                            if count > 100:
                                break
                            self._show_package(pkg, INFO_INSTALLED)
                else:
                    available.append(pkg)

        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

        # Now show available packages.
        if FILTER_INSTALLED not in fltlist:
            for pkg in available:
                if self._do_extra_filtering(pkg,fltlist):
                    self._show_package(pkg, INFO_AVAILABLE)

    def _do_extra_filtering(self,pkg,filterList):
        ''' do extra filtering (gui,devel etc) '''
        for filter in filterList:
            if filter in (FILTER_INSTALLED, FILTER_NOT_INSTALLED):
                continue
            elif filter in (FILTER_GUI, FILTER_NOT_GUI):
                if not self._do_gui_filtering(filter, pkg):
                    return False
            elif filter in (FILTER_DEVELOPMENT, FILTER_NOT_DEVELOPMENT):
                if not self._do_devel_filtering(filter, pkg):
                    return False
            elif filter in (FILTER_FREE, FILTER_NOT_FREE):
                if not self._do_free_filtering(filter, pkg):
                    return False
        return True

    def _do_gui_filtering(self,flt,pkg):
        isGUI = False
        if flt == FILTER_GUI:
            wantGUI = True
        else:
            wantGUI = False
        isGUI = self._check_for_gui(pkg)
        return isGUI == wantGUI

    def _check_for_gui(self,pkg):
        '''  Check if the GUI_KEYS regex matches any package requirements'''
        try:
            for req in pkg.requires:
                reqname = req[0]
                if GUI_KEYS.search(reqname):
                    return True
            return False
        except yum.Errors.RepoError,e:
            self.ErrorCode(ERROR_NO_CACHE,"Yum cache is invalid")
            self.Exit()

    def _do_devel_filtering(self,flt,pkg):
        isDevel = False
        if flt == FILTER_DEVELOPMENT:
            wantDevel = True
        else:
            wantDevel = False
        regex =  re.compile(r'(-devel)|(-dgb)|(-static)')
        if regex.search(pkg.name):
            isDevel = True
        return isDevel == wantDevel

    def _do_free_filtering(self,flt,pkg):
        isFree = False
        if flt == FILTER_FREE:
            wantFree = True
        else:
            wantFree = False

        isFree = self.check_license_field(pkg.license)

        return isFree == wantFree

    def _buildGroupDict(self):
        pkgGroups= {}
        cats = self.yumbase.comps.categories
        for cat in cats:
            grps = map( lambda x: self.yumbase.comps.return_group( x ),
               filter( lambda x: self.yumbase.comps.has_group( x ), cat.groups ) )
            grplist = []
            for group in grps:
                for pkg in group.mandatory_packages.keys():
                    pkgGroups[pkg] = "%s;%s" % (cat.categoryid,group.groupid)
                for pkg in group.default_packages.keys():
                    pkgGroups[pkg] = "%s;%s" % (cat.categoryid,group.groupid)
                for pkg in group.optional_packages.keys():
                    pkgGroups[pkg] = "%s;%s" % (cat.categoryid,group.groupid)
                for pkg in group.conditional_packages.keys():
                    pkgGroups[pkg] = "%s;%s" % (cat.categoryid,group.groupid)
        return pkgGroups

    def _show_package_description(self,pkg):        
        pkgver = self._get_package_ver(pkg)
        id = self.get_package_id(pkg.name, pkgver, pkg.arch, pkg.repo)
        desc = pkg.description
        desc = desc.replace('\n\n',';')
        desc = desc.replace('\n',' ')

        self._show_description(id, pkg.license, "unknown", desc, pkg.url,
                             pkg.size)

    def _getEVR(self,idver):
        '''
        get the e,v,r from the package id version
        '''
        cpos = idver.find(':')
        if cpos != -1:
            epoch = idver[:cpos]
            idver = idver[cpos+1:]
        else:
            epoch = '0'
        (version,release) = tuple(idver.split('-'))
        return epoch,version,release

    def _findPackage(self,id):
        '''
        find a package based on a package id (name;version;arch;repoid)
        '''
        # Split up the id
        (n,idver,a,d) = self.get_package_from_id(id)
        # get e,v,r from package id version
        e,v,r = self._getEVR(idver)
        # search the rpmdb for the nevra
        pkgs = self.yumbase.rpmdb.searchNevra(name=n,epoch=e,ver=v,rel=r,arch=a)
        # if the package is found, then return it
        if len(pkgs) != 0:
            return pkgs[0],True
        # search the pkgSack for the nevra
        pkgs = self.yumbase.pkgSack.searchNevra(name=n,epoch=e,ver=v,rel=r,arch=a)
        # if the package is found, then return it
        if len(pkgs) != 0:
            return pkgs[0],False
        else:
            return None,False

    def _is_inst(self,pkg):
        return self.yumbase.rpmdb.installed(po=pkg)

    def _installable(self, pkg, ematch=False):

        """check if the package is reasonably installable, true/false"""

        exactarchlist = self.yumbase.conf.exactarchlist
        # we look through each returned possibility and rule out the
        # ones that we obviously can't use

        if self._is_inst(pkg):
            return False

        # everything installed that matches the name
        installedByKey = self.yumbase.rpmdb.searchNevra(name=pkg.name)
        comparable = []
        for instpo in installedByKey:
            if rpmUtils.arch.isMultiLibArch(instpo.arch) == rpmUtils.arch.isMultiLibArch(pkg.arch):
                comparable.append(instpo)
            else:
                continue

        # go through each package
        if len(comparable) > 0:
            for instpo in comparable:
                if pkg.EVR > instpo.EVR: # we're newer - this is an update, pass to them
                    if instpo.name in exactarchlist:
                        if pkg.arch == instpo.arch:
                            return True
                    else:
                        return True

                elif pkg.EVR == instpo.EVR: # same, ignore
                    return False

                elif pkg.EVR < instpo.EVR: # lesser, check if the pkgtup is an exactmatch
                                   # if so then add it to be installed
                                   # if it can be multiply installed
                                   # this is where we could handle setting
                                   # it to be an 'oldpackage' revert.

                    if ematch and self.yumbase.allowedMultipleInstalls(pkg):
                        return True

        else: # we've not got any installed that match n or n+a
            return True

        return False

    def _get_best_dependencies(self,po):
        ''' find the most recent packages that provides the dependencies for a package
        @param po: yum package object to find deps for
        @return: a list for yum package object providing the dependencies
        '''
        results = self.yumbase.findDeps([po])
        pkg = results.keys()[0]
        bestdeps=[]
        if len(results[pkg].keys()) == 0: # No dependencies for this package ?
            return bestdeps
        for req in results[pkg].keys():
            reqlist = results[pkg][req]
            if not reqlist: #  Unsatisfied dependency
                self.ErrorCode(ERROR_DEP_RESOLUTION_FAILED,"the (%s) requirement could not be resolved" % prco_tuple_to_string(req))
                continue
            best = None
            for po in reqlist:
                if best:
                    if po.EVR > best.EVR:
                        best=po
                else:
                    best= po
            bestdeps.append(best)
        return unique(bestdeps)

    def _localInstall(self, inst_file):
        """handles installs/updates of rpms provided on the filesystem in a
           local dir (ie: not from a repo)"""

        # Slightly modified localInstall from yum's cli.py

        # read in each package into a YumLocalPackage Object
        # append it to self.yumbase.localPackages
        # check if it can be installed or updated based on nevra versus rpmdb
        # don't import the repos until we absolutely need them for depsolving

        oldcount = len(self.yumbase.tsInfo)

        installpkgs = []
        updatepkgs = []

        pkg = inst_file
        try:
            po = yum.packages.YumLocalPackage(ts=self.yumbase.rpmdb.readOnlyTS(), filename=pkg)
        except yum.Errors.MiscError:
            self.ErrorCode(ERROR_INTERNAL_ERROR,'Cannot open file: %s. Skipping.' % pkg)
            self.Exit()

        # everything installed that matches the name
        installedByKey = self.yumbase.rpmdb.searchNevra(name=po.name)
        # go through each package
        if len(installedByKey) == 0: # nothing installed by that name
            installpkgs.append(po)
        else:
            for installed_pkg in installedByKey:
                if po.EVR > installed_pkg.EVR: # we're newer - this is an update, pass to them
                    if installed_pkg.name in self.yumbase.conf.exactarchlist:
                        if po.arch == installed_pkg.arch:
                            updatepkgs.append((po, installed_pkg))
                            continue
                        else:
                            continue
                    else:
                        updatepkgs.append((po, installed_pkg))
                        continue
                elif po.EVR == installed_pkg.EVR:
                    if po.arch != installed_pkg.arch and (isMultiLibArch(po.arch) or
                              isMultiLibArch(installed_pkg.arch)):
                        installpkgs.append(po)
                        continue
                    else:
                        continue
                else:
                    continue

        # handle excludes for a localinstall
        toexc = []
        if len(self.yumbase.conf.exclude) > 0:
           exactmatch, matched, unmatched = \
                   yum.packages.parsePackages(installpkgs + map(lambda x: x[0], updatepkgs),
                                 self.yumbase.conf.exclude, casematch=1)
           toexc = exactmatch + matched

        # Process potential installs
        for po in installpkgs:
            if po in toexc:
               continue     # Exclude package
            # Add package to transaction for installation
            self.yumbase.localPackages.append(po)
            self.yumbase.install(po=po)
        # Process potential updates
        for (po, oldpo) in updatepkgs:
            if po in toexc:
               continue # Excludeing package
            # Add Package to transaction for updating
            self.yumbase.localPackages.append(po)
            self.yumbase.tsInfo.addUpdate(po, oldpo)

    def _check_for_reboot(self):
        md = self.updateMetadata
        for txmbr in self.yumbase.tsInfo:
            pkg = txmbr.po
            # check if package is in reboot list or flagged with reboot_suggested
            # in the update metadata and is installed/updated etc
            notice = md.get_notice((pkg.name, pkg.version, pkg.release))
            if (pkg.name in self.rebootpkgs \
                or (notice and notice.get_metadata().has_key('reboot_suggested') and notice['reboot_suggested']))\
                and txmbr.ts_state in TS_INSTALL_STATES:
                self.require_restart(RESTART_SYSTEM,"")
                break

    def _runYumTransaction(self,removedeps=None):
        '''
        Run the yum Transaction
        This will only work with yum 3.2.4 or higher
        '''
        rc,msgs =  self.yumbase.buildTransaction()
        if rc !=2:
            retmsg = "Error in Dependency Resolution;" +";".join(msgs)
            self.ErrorCode(ERROR_DEP_RESOLUTION_FAILED,retmsg)
            self.Exit()
        else:
            self._check_for_reboot()
            if removedeps == False:
                if len(self.yumbase.tsInfo) > 1:
                    retmsg = 'package could not be remove, because something depends on it'
                    self.ErrorCode(ERROR_DEP_RESOLUTION_FAILED,retmsg)
                    self.Exit()

            try:
                rpmDisplay = PackageKitCallback(self)
                callback = ProcessTransPackageKitCallback(self)
                self.yumbase.processTransaction(callback=callback,
                                      rpmDisplay=rpmDisplay)
            except yum.Errors.YumDownloadError, ye:
                retmsg = "Error in Download;" +";".join(ye.value)
                self.ErrorCode(ERROR_PACKAGE_DOWNLOAD_FAILED,retmsg)
                self.Exit()
            except yum.Errors.YumGPGCheckError, ye:
                retmsg = "Error in Package Signatures;" +";".join(ye.value)
                self.ErrorCode(ERROR_INTERNAL_ERROR,retmsg)
                self.Exit()
            except GPGKeyNotImported, e:
                keyData = self.yumbase.missingGPGKey
                if not keyData:
                    self.ErrorCode(ERROR_INTERNAL_ERROR,
                               "GPG key not imported, but no GPG information received from Yum.")
                    self.Exit()
                self.repo_signature_required(keyData['po'].repoid,
                                             keyData['keyurl'],
                                             keyData['userid'],
                                             keyData['hexkeyid'],
                                             keyData['fingerprint'],
                                             keyData['timestamp'],
                                             'GPG')
                self.ErrorCode(ERROR_GPG_FAILURE,"GPG key not imported.")
                self.Exit()
            except yum.Errors.YumBaseError, ye:
                retmsg = "Error in Transaction Processing;" +";".join(ye.value)
                self.ErrorCode(ERROR_TRANSACTION_ERROR,retmsg)
                self.Exit()

    def _get_status(self,notice):
        ut = notice['type']
        if ut == 'security':
            return INFO_SECURITY
        elif ut == 'bugfix':
            return INFO_BUGFIX
        elif ut == 'enhancement':
            return INFO_ENHANCEMENT
        else:
            return INFO_UNKNOWN

    def _get_obsoleted(self,name):
        obsoletes = self.yumbase.up.getObsoletesTuples( newest=1 )
        for ( obsoleting, installed ) in obsoletes:
            if obsoleting[0] == name:
                pkg =  self.yumbase.rpmdb.searchPkgTuple( installed )[0]
                return self._pkg_to_id(pkg)
        return ""

    def _get_updated(self,pkg):
        updated = None
        pkgs = self.yumbase.rpmdb.searchNevra(name=pkg.name)
        if pkgs:
            return self._pkg_to_id(pkgs[0])
        else:
            return ""

    def _get_update_metadata(self):
        if not self._updateMetadata:
            self._updateMetadata = UpdateMetadata()
            for repo in self.yumbase.repos.listEnabled():
                try:
                    self._updateMetadata.add(repo)
                except:
                    pass # No updateinfo.xml.gz in repo
        return self._updateMetadata

    _updateMetadata = None
    updateMetadata = property(fget=_get_update_metadata)

    def _format_str(self,str):
        """
        Convert a multi line string to a list separated by ';'
        """
        if str:
            lines = str.split('\n')
            return ";".join(lines)
        else:
            return ""

    def _format_list(self,lst):
        """
        Convert a multi line string to a list separated by ';'
        """
        if lst:
            return ";".join(lst)
        else:
            return ""

    def _get_update_extras(self,pkg):
        md = self.updateMetadata
        notice = md.get_notice((pkg.name, pkg.version, pkg.release))
        urls = {'bugzilla':[], 'cve' : [], 'vendor': []}
        if notice:
            # Update Description
            desc = notice['description']
            # Update References (Bugzilla,CVE ...)
            refs = notice['references']
            if refs:
                for ref in refs:
                    typ = ref['type']
		    href = ref['href']
		    title = ref['title']
                    if typ in ('bugzilla','cve') and href != None:
			if title == None:
			    title = ""
                        urls[typ].append("%s;%s" % (href,title))
                    else:
                        urls['vendor'].append("%s;%s" % (ref['href'],ref['title']))

            # Reboot flag
            if notice.get_metadata().has_key('reboot_suggested') and notice['reboot_suggested']:
				reboot = 'system'
            else:
                reboot = 'none'
            return self._format_str(desc),urls,reboot
        else:
            return "",urls,"none"

#
# Other utility methods
#

    def _get_package_ver(self,po):
        ''' return the a ver as epoch:version-release or version-release, if epoch=0'''
        if po.epoch != '0':
            ver = "%s:%s-%s" % (po.epoch,po.version,po.release)
        else:
            ver = "%s-%s" % (po.version,po.release)
        return ver


    def _setup_yum(self):
        self.yumbase.doConfigSetup(errorlevel=0,debuglevel=0)     # Setup Yum Config
        self.yumbase.conf.throttle = "40%"                        # Set bandwidth throttle to 40%
        self.dnlCallback = DownloadCallback(self,showNames=True)  # Download callback
        self.yumbase.repos.setProgressBar( self.dnlCallback )     # Setup the download callback class

class DownloadCallback( BaseMeter ):
    """ Customized version of urlgrabber.progress.BaseMeter class """
    def __init__(self,base,showNames = False):
        BaseMeter.__init__( self )
        self.totSize = ""
        self.base = base
        self.showNames = showNames
        self.oldName = None
        self.lastPct = 0
        self.totalPct = 0
        self.pkgs = None
        self.numPkgs=0
        self.bump = 0.0

    def setPackages(self,pkgs,startPct,numPct):
        self.pkgs = pkgs
        self.numPkgs = float(len(self.pkgs))
        self.bump = numPct/self.numPkgs
        self.totalPct = startPct

    def _getPackage(self,name):
        if self.pkgs:
            for pkg in self.pkgs:
                rpmfn = os.path.basename(pkg.remote_path) # get the rpm filename of the package
                if rpmfn == name:
                    return pkg
        return None

    def update( self, amount_read, now=None ):
        BaseMeter.update( self, amount_read, now )

    def _do_start( self, now=None ):
        name = self._getName()
        self.updateProgress(name,0.0,"","")
        if not self.size is None:
            self.totSize = format_number( self.size )

    def _do_update( self, amount_read, now=None ):
        fread = format_number( amount_read )
        name = self._getName()
        if self.size is None:
            # Elapsed time
            etime = self.re.elapsed_time()
            fetime = format_time( etime )
            frac = 0.0
            self.updateProgress(name,frac,fread,fetime)
        else:
            # Remaining time
            rtime = self.re.remaining_time()
            frtime = format_time( rtime )
            frac = self.re.fraction_read()
            self.updateProgress(name,frac,fread,frtime)

    def _do_end( self, amount_read, now=None ):
        total_time = format_time( self.re.elapsed_time() )
        total_size = format_number( amount_read )
        name = self._getName()
        self.updateProgress(name,1.0,total_size,total_time)

    def _getName(self):
        '''
        Get the name of the package being downloaded
        '''
        if self.text and type( self.text ) == type( "" ):
            name = self.text
        else:
            name = self.basename
        return name

    def updateProgress(self,name,frac,fread,ftime):
        '''
         Update the progressbar (Overload in child class)
        @param name: filename
        @param frac: Progress fracment (0 -> 1)
        @param fread: formated string containing BytesRead
        @param ftime : formated string containing remaining or elapsed time
        '''
        pct = int( frac*100 )
        if name != self.oldName: # If this a new package
            if self.oldName:
                self.base.SubPercentageChanged(100)
            self.oldName = name
            if self.bump > 0.0: # Bump the total download percentage
                self.totalPct += self.bump
                self.lastPct = 0
                self.base.PercentageChanged(int(self.totalPct))
            if self.showNames:
                pkg = self._getPackage(name)
                if pkg: # show package to download
                    self.base._show_package(pkg,INFO_DOWNLOADING)
                else:
                    if name in MetaDataMap:
                        typ = MetaDataMap[name]
                    else:
                        typ = 'unknown'
                    self.base.metadata(typ,name)
            self.base.SubPercentageChanged(0)
        else:
            if self.lastPct != pct and pct != 0 and pct != 100:
	            self.lastPct = pct
	            # bump the sub persentage for this package
	            self.base.SubPercentageChanged(pct)

class PackageKitCallback(RPMBaseCallback):
    def __init__(self,base):
        RPMBaseCallback.__init__(self)
        self.base = base
        self.pct = 0
        self.curpkg = None
        self.startPct = 50
        self.numPct = 50
        # Map yum transactions with pk info enums
        self.info_actions = { TS_UPDATE : INFO_UPDATING,
                        TS_ERASE: INFO_REMOVING,
                        TS_INSTALL: INFO_INSTALLING,
                        TS_TRUEINSTALL : INFO_INSTALLING,
                        TS_OBSOLETED: INFO_OBSOLETING,
                        TS_OBSOLETING: INFO_INSTALLING,
                        TS_UPDATED: INFO_CLEANUP}

        # Map yum transactions with pk state enums
        self.state_actions = { TS_UPDATE : STATUS_UPDATE,
                        TS_ERASE: STATUS_REMOVE,
                        TS_INSTALL: STATUS_INSTALL,
                        TS_TRUEINSTALL : STATUS_INSTALL,
                        TS_OBSOLETED: STATUS_OBSOLETE,
                        TS_OBSOLETING: STATUS_INSTALL,
                        TS_UPDATED: STATUS_CLEANUP}

    def _calcTotalPct(self,ts_current,ts_total):
        bump = float(self.numPct)/ts_total
        pct = int(self.startPct + (ts_current * bump))
        return pct

    def _showName(self,status):
        if type(self.curpkg) in types.StringTypes:
            id = self.base._get_package_id(self.curpkg,'','','')
        else:
            pkgver = self.base._get_package_ver(self.curpkg)
            id = self.base._get_package_id(self.curpkg.name, pkgver, self.curpkg.arch, self.curpkg.repo)
        self.base.Package(status, id, "")

    def event(self, package, action, te_current, te_total, ts_current, ts_total):
        if str(package) != str(self.curpkg):
            self.curpkg = package
            self.base.StatusChanged(self.state_actions[action])
            self._showName(self.info_actions[action])
            pct = self._calcTotalPct(ts_current, ts_total)
            self.base.PercentageChanged(pct)
        val = (ts_current*100L)/ts_total
        if val != self.pct:
            self.pct = val
            self.base.SubPercentageChanged(val)

    def errorlog(self, msg):
        # grrrrrrrr
        pass

class ProcessTransPackageKitCallback:
    def __init__(self,base):
        self.base = base

    def event(self,state,data=None):
        if state == PT_DOWNLOAD:        # Start Downloading
            self.base.AllowCancel(True)
            self.base.PercentageChanged(10)
            self.base.StatusChanged(STATUS_DOWNLOAD)
        if state == PT_DOWNLOAD_PKGS:   # Packages to download
            self.base.dnlCallback.setPackages(data,10,30)
        elif state == PT_GPGCHECK:
            self.base.PercentageChanged(40)
            pass
        elif state == PT_TEST_TRANS:
            self.base.AllowCancel(False)
            self.base.PercentageChanged(45)
            pass
        elif state == PT_TRANSACTION:
            self.base.AllowCancel(False)
            self.base.PercentageChanged(50)
            pass

class PackageKitYumBase(yum.YumBase):
    """
    Subclass of YumBase.  Needed so we can overload _checkSignatures
    and nab the gpg sig data
    """

    def __init__(self):
        yum.YumBase.__init__(self)
        self.missingGPGKey = None

    def _checkSignatures(self,pkgs,callback):
        ''' The the signatures of the downloaded packages '''
        # This can be overloaded by a subclass.

        for po in pkgs:
            result, errmsg = self.sigCheckPkg(po)
            if result == 0:
                # Verified ok, or verify not req'd
                continue
            elif result == 1:
                self.getKeyForPackage(po, fullaskcb=self._fullAskForGPGKeyImport)
            else:
                raise yum.Errors.YumGPGCheckError, errmsg

        return 0

    def _fullAskForGPGKeyImport(self, data):
        self.missingGPGKey = data

        raise GPGKeyNotImported()

    def _askForGPGKeyImport(self, po, userid, hexkeyid):
        '''
        Ask for GPGKeyImport
        '''
        # TODO: Add code here to send the RepoSignatureRequired signal
        return False

if __name__ == '__main__':
    loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus(mainloop=loop)
    bus_name = dbus.service.BusName(PACKAGEKIT_DBUS_SERVICE, bus=bus)
    manager = PackageKitYumBackend(bus_name, PACKAGEKIT_DBUS_PATH)

