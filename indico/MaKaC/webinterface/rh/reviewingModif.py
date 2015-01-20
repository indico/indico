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

import os

from MaKaC.errors import MaKaCError
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
from MaKaC.webinterface.pages.reviewing import WPConfModifReviewingPaperSetup
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.i18n import _
from indico.util import json
from indico.web.flask.util import send_file


class RCPaperReviewManager:
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a PRM of the conference
        """
        return request._conf.getConfPaperReview().isPaperReviewManager(request.getAW().getUser())


class RCReviewingStaff:
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a PRM, an AM, a referee, an editor, a reviewer or an abstract reviewer of the conference
        """
        return request._conf.getConfPaperReview().isInReviewingTeam(request.getAW().getUser())

class RCReferee:
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a referee of the conference
        """
        return request._conf.getConfPaperReview().isReferee(request.getAW().getUser())

class RCEditor:
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is an editor of the conference
        """
        return request._conf.getConfPaperReview().isEditor(request.getAW().getUser())

class RCReviewer:
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a reviewer of the conference
        """
        return request._conf.getConfPaperReview().isReviewer(request.getAW().getUser())

class RHConfModifReviewingAccess(RHConferenceModifBase):
    """ Class used when the user clicks on the main 'Reviewing' tab
        Depending if the user is PRM or AM, etc. the user will be redirected
        to one of the subtabs of the reviewing tab.
        This is needed because depending on the role of the user,
        they cannot see some of the subtabs and then they need to be
        redirected to the appropiate subtab.
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._isPRM = RCPaperReviewManager.hasRights(self)
        self._isReferee = RCReferee.hasRights(self)
        self._isReviewingStaff = RCReviewingStaff.hasRights(self)
        self._isEditor = RCEditor.hasRights(self)
        self._isReviewer = RCReviewer.hasRights(self)

    def _checkProtection(self):
        if not self._isReviewingStaff:
            RHConferenceModifBase._checkProtection(self)

    def _process( self ):

        if hasattr(self, "_redirectURL") and self._redirectURL != "":
            url = self._redirectURL
        elif self._isPRM:
            url = urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf )
        elif self._isReferee:
            url = urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf )
        elif self._isReviewer:
            url = urlHandlers.UHConfModifListContribToJudgeAsReviewer.getURL( self._conf )
        elif self._isEditor:
            url = urlHandlers.UHConfModifListContribToJudgeAsEditor.getURL( self._conf )
        elif self._isReviewingStaff:
            url= urlHandlers.UHConfModifListContribToJudge.getURL( self._conf )

        else: #we leave this else just in case
            url = urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf )

        self._redirect( url )

class RHConfModifReviewingPRMBase (RHConferenceModifBase):
    """ Base class that allows only paper review managers to do this request.
        If user is not a paper review manager, they need to be a conference manager.
    """

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if not RCPaperReviewManager.hasRights(self):
                RHConferenceModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))


class RHConfModifReviewingPRMAMBase (RHConferenceModifBase):
    """ Base class that allows only paper review managers OR abstract managers to do this request.
        If user is not a paper review manager, they need to be a conference manager.
    """

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            if not RCPaperReviewManager.hasRights(self):
                RHConferenceModifBase._checkProtection(self);
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))



class RHConfModifReviewingPaperSetup( RHConfModifReviewingPRMBase ):
    """ Class used when the user clicks on the Paper Setup
        subtab of the Reviewing tab
    """
    _uh = urlHandlers.UHConfModifReviewingPaperSetup

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
        else:
            p = WPConfModifReviewingPaperSetup( self, self._target)
        return p.display()


class RHSetTemplate(RHConfModifReviewingPRMBase):
    _uh = urlHandlers.UHSetTemplate

    def _checkParams( self, params ):
        RHConfModifReviewingPRMBase._checkParams( self, params )
        self._name = params.get("name")
        self._description = params.get("description")
        self._templateId = params.get("temlId")
        if ("format" in params):
            self._format = params.get("format")
        else:
            self._format = params.get("formatOther")
        try:
            self._templatefd = params.get("file").file
        except AttributeError:
            raise MaKaCError("Problem when storing template file")
        self._ext = os.path.splitext(params.get("file").filename)[1] or '.template'

    def _process( self ):
        import random
        self._id = str(random.random()*random.randint(1,32768))
        if self._templatefd == None:
            return {'status': 'ERROR'}
        else:
            self._conf.getConfPaperReview().setTemplate(self._name, self._description, self._format, self._templatefd, self._id, self._ext)
            #self._redirect( urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf ) )
            return json.dumps({
                'status': 'OK',
                'info': {
                    'name': self._name,
                    'description': self._description,
                    'format': self._format,
                    'id': self._id
                }
            }, textarea=True)

class RHDownloadTemplate(RHConferenceBaseDisplay):

    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            RHConferenceBaseDisplay._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))


    def _checkParams(self, params):
        RHConferenceBase._checkParams( self, params )
        self._templateId = params.get("reviewingTemplateId")

    def _process(self):
        template = self._target.getConfPaperReview().getTemplates()[self._templateId].getFile()
        return send_file(template.getFileName(), template.getFilePath(), template.getFileType())
