# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.
import uuid

from MaKaC import *
import ZODB
from persistent import Persistent
from persistent.mapping import PersistentMapping
from BTrees import OOBTree
import MaKaC.common.info as info

import base
from MaKaC.common import DBMgr
from MaKaC.common.logger import Logger


class PSession( base.Session, Persistent ):
    """
    Keys which are already used in the data dictionary of each session:
        - menuStatus: it is used for knowing if the conference display menu is closed or opened.
        - accessKeys: contains all the access keys entered by the user in this session
        - modifKeys: contains all the modification keys entered by the user in this session
    """

    def __init__(self, request, id):
        base.Session.__init__(self, request, id)
        self.user = None
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        self.datadict = PersistentMapping()
        base.Session.__init__(self, request, id)
        self._lang = minfo.getLang()
        self.datadict["ActiveTimezone"] = "LOCAL"

    @property
    def csrf_token(self):
        try:
            return self._csrf_token
        except AttributeError:
            self._csrf_token = str(uuid.uuid4())
            return self._csrf_token

    def reset_csrf_token(self):
        if hasattr(self, '_csrf_token'):
            del self._csrf_token

    @property
    def csrf_protected(self):
        """Does the session need CSRF protection?"""
        return self.user is not None

    def has_info (self):
        """has_info() -> boolean

        Return true if this session contains any information that must
        be saved.
        """
        # This flag will indicate when to commit a session
        return getattr(self, '_v_modified', False)

    def setUser( self, newUser ):
        if newUser:
            self._lang = newUser.getLang()
        self.user = newUser
        self.reset_csrf_token()
        self._v_modified = True

    def getUser( self ):
        return self.user

    def getId( self ):
        return self.id

    def setVar(self, key, value):
        try:
            self.datadict[key] = value
        except AttributeError:
            self.datadict = PersistentMapping()
            self.datadict[key] = value
        self._v_modified = True

    def getVar(self, key):
        try:
            if self.datadict:
                pass
        except AttributeError:
            self.datadict = PersistentMapping()
            return None
        return self.datadict.get(key,None)

    def removeVar(self, key):
        try:
            if self.datadict:
                pass
        except AttributeError:
            self.datadict = PersistentMapping()
            return None
        if self.datadict.has_key(key):
            del self.datadict[key]
            self._v_modified = True

    def getLang(self):
        try:
            if self._lang is None:
                raise Exception("no language")
        except:
            try:
                lang=self.user.getLang()
            except:
                lang="en_GB"
                Logger.get('i18n').debug('No user language defined. Using %s as default.' % lang)
            self._lang = lang

        return self._lang

    def setLang(self, lang):
        self._lang = lang
        self._v_modified = True

    def _p_resolveConflict(self, oldState, savedState, newState):
        """
        ZODB Conflict resolution
        Basically, all the atributes are taken from the conflicting
        transaction ("this one"), except for the creation time, which
        is max(T1,T2)
        """

        # Language, user and address are overwritten
        savedState['_lang'] = newState.get('_lang', None)
        savedState['user'] = newState.get('user', None)
        savedState['__remote_address'] = newState.get('__remote_address', None)

        # access time will be the latest

        savedState['__creation_time'] = max(newState.get('__creation_time', 0),
                                            savedState.get('__creation_time', 0))

        return oldState


class PSessionManager( base.MPSessionManager, Persistent ):

    def __init__( self ):
        base.MPSessionManager.__init__( self, PSession, OOBTree.OOBTree() )

#helper function
#   this should go in a PSessionManager static method but the fact that it
#   inherits from Persistent, becoming therefore an extension class, seems
#   to make it not possible to use static/class methods. To be changed when
#   ZODB migrates Persistent to non-extension classes
def getSessionManager(debug=0):
    root = DBMgr.getInstance().getDBConnection().root()
    try:
        sm = root["SessionManagers"]["main"]
    except KeyError, e:
        sm = PSessionManager()
        root["SessionManagers"] = OOBTree.OOBTree()
        root["SessionManagers"]["main"] = sm
    return sm




if __name__ == "__main__":
    sm = PSessionManager()
    print sm
