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

import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceBase import RHFileBase, RHLinkBase
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.pages import files
from MaKaC.common import Config
from MaKaC.errors import NotFoundError, AccessError

from MaKaC.conference import Reviewing, Link
from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff
from copy import copy

from indico.web.flask.util import send_file


class RHFileAccess(RHFileBase, RHDisplayBaseProtected):
    _uh  = urlHandlers.UHFileAccess

    def _checkParams( self, params ):
        try:
            RHFileBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you try to access does not exist.")

    def _checkProtection( self ):
        if isinstance(self._file.getOwner(), Reviewing):
            selfcopy = copy(self)
            selfcopy._target = self._file.getOwner().getContribution()
            if not (RCContributionPaperReviewingStaff.hasRights(selfcopy) or \
                selfcopy._target.canUserSubmit(self.getAW().getUser()) or \
                self._target.canModify( self.getAW() )):
                raise AccessError()
        else:
            RHDisplayBaseProtected._checkProtection( self )

    def _process( self ):
        self._notify('materialDownloaded', self._file)
        if isinstance(self._file, Link):
            self._redirect(self._file.getURL())
        elif self._file.getId() == "minutes":
            p = files.WPMinutesDisplay(self, self._file )
            return p.display()
        else:
            return send_file(self._file.getFileName(), self._file.getFilePath(), self._file.getFileType(),
                             self._file.getCreationDate())


class RHFileAccessStoreAccessKey( RHFileBase ):
    _uh = urlHandlers.UHFileEnterAccessKey

    def _checkParams( self, params ):
        RHFileBase._checkParams(self, params )
        self._accesskey = params.get( "accessKey", "" ).strip()

    def _checkProtection( self ):
        pass

    def _process( self ):
        access_keys = self._getSession().getVar("accessKeys")
        if access_keys == None:
            access_keys = {}
        access_keys[self._target.getOwner().getUniqueId()] = self._accesskey
        self._getSession().setVar("accessKeys",access_keys)
        url = urlHandlers.UHFileAccess.getURL( self._target )
        self._redirect( url )


class RHVideoWmvAccess( RHLinkBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHVideoWmvAccess

    def _checkParams( self, params ):
        try:
            RHLinkBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you try to access does not exist.")

    def _checkProtection( self ):
        """targets for this RH are exclusively URLs so no protection apply"""
        return

    def _process( self ):
        p = files.WPVideoWmv(self, self._link )
        return p.display()

class RHVideoFlashAccess( RHLinkBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHVideoFlashAccess

    def _checkParams( self, params ):
        try:
            RHLinkBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you try to access does not exist.")

    def _checkProtection( self ):
        """targets for this RH are exclusively URLs so no protection apply"""
        return

    def _process( self ):
        p = files.WPVideoFlash(self, self._link )
        return p.display()
