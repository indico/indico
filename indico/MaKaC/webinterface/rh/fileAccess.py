# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from flask import session

import os
from copy import copy
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.rh.conferenceBase import RHFileBase, RHLinkBase
from MaKaC.webinterface.rh.base import RH, RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.pages import files
from MaKaC.errors import NotFoundError, AccessError
from MaKaC.registration import Registrant
from MaKaC.conference import Reviewing, Link
from MaKaC.webinterface.rh.contribMod import RCContributionPaperReviewingStaff
from MaKaC.i18n import _

from indico.web.flask.util import send_file
from indico.modules import ModuleHolder


class RHFileAccess(RHFileBase, RHDisplayBaseProtected):
    _uh  = urlHandlers.UHFileAccess

    def _checkParams( self, params ):
        try:
            RHFileBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you tried to access does not exist.")

    def _checkProtection( self ):
        if isinstance(self._file.getOwner(), Reviewing):
            selfcopy = copy(self)
            selfcopy._target = self._file.getOwner().getContribution()
            if not (RCContributionPaperReviewingStaff.hasRights(selfcopy) or \
                selfcopy._target.canUserSubmit(self.getAW().getUser()) or \
                self._target.canModify( self.getAW() )):
                raise AccessError()
        elif isinstance(self._file.getOwner(), Registrant) and \
             not self._file.getOwner().canUserModify(self.getAW().getUser()):
            raise AccessError(_("Access to this resource is forbidden."))

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


class RHFileAccessStoreAccessKey(RHFileBase):
    _uh = urlHandlers.UHFileEnterAccessKey

    def _checkParams(self, params):
        RHFileBase._checkParams(self, params)
        self._accesskey = params.get("accessKey", "").strip()
        self._doNotSanitizeFields.append("accessKey")

    def _checkProtection(self):
        pass

    def _process(self):
        access_keys = session.setdefault('accessKeys', {})
        access_keys[self._target.getOwner().getUniqueId()] = self._accesskey
        session.modified = True
        self._redirect(urlHandlers.UHFileAccess.getURL(self._target))


class RHVideoWmvAccess( RHLinkBase, RHDisplayBaseProtected ):
    _uh  = urlHandlers.UHVideoWmvAccess

    def _checkParams( self, params ):
        try:
            RHLinkBase._checkParams( self, params )
        except:
            raise NotFoundError("The file you tried to access does not exist.")

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
            raise NotFoundError("The file you tried to access does not exist.")

    def _checkProtection( self ):
        """targets for this RH are exclusively URLs so no protection apply"""
        return

    def _process( self ):
        p = files.WPVideoFlash(self, self._link )
        return p.display()


class RHOfflineEventAccess(RHConferenceModifBase):
    _uh = urlHandlers.UHOfflineEventAccess

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        if 'fileId' not in params:
            raise NotFoundError(_("Missing 'fileId' argument."))
        self._offlineEvent = ModuleHolder().getById("offlineEvents").getOfflineEventByFileId(params["confId"],
                                                                                             params["fileId"])
        if not self._offlineEvent or not self._offlineEvent.file or \
           not os.path.isfile(self._offlineEvent.file.getFilePath()):
            raise NotFoundError(_("The file you tried to access does not exist anymore."))

    def _process(self):
        f = self._offlineEvent.file
        return send_file('event-%s.zip' % self._conf.getId(), f.getFilePath(), f.getFileType(),
                         last_modified=self._offlineEvent.creationTime, inline=False)
