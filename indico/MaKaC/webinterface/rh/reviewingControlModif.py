# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
import MaKaC.webinterface.pages.reviewing as reviewing
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed
import MaKaC.user as user
from MaKaC.webinterface.rh.reviewingModif import RHConfModifReviewingPRMAMBase,\
    RHConfModifReviewingPRMBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.errors import MaKaCError
from MaKaC.paperReviewing import ConferencePaperReview as CPR

#class to display the page
class RHConfModifReviewingControl( RHConfModifReviewingPRMAMBase ):
    _uh = urlHandlers.UHConfModifReviewingControl

    def _checkParams( self, params ):
        RHConfModifReviewingPRMAMBase._checkParams( self, params )

    def _process( self ):
        if self._conf.isClosed():
            p = WPConferenceModificationClosed( self, self._target )
        else:
            p = reviewing.WPConfModifReviewingControl( self, self._target)
        return p.display()


class RHConfModifReviewingBase(RHConferenceModifBase):
    """ Base class that checks if reviewing module is active
    """
    def _checkProtection(self):
        if self._target.hasEnabledSection("paperReviewing"):
            RHConferenceModifBase._checkProtection(self)
        else:
            raise MaKaCError(_("Paper Reviewing is not active for this conference"))


#Paper Review Manager classes
class RHConfSelectPaperReviewManager( RHConfModifReviewingBase ):
    """
    Only conference managers can add paper review managers,
    so this class inherits from RHConferenceModifBase
    """
    _uh = urlHandlers.UHConfSelectPaperReviewManager

    def _process( self ):
        p = reviewing.WPConfSelectPaperReviewManager( self, self._target )
        return p.display( **self._getRequestParams() )


class RHConfAddPaperReviewManager( RHConfModifReviewingBase ):
    """
    Only conference managers can add paper review managers,
    so this class inherits from RHConferenceModifBase
    """

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().addPaperReviewManager( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )


class RHConfRemovePaperReviewManager( RHConfModifReviewingBase ):
    """
    Only conference managers can remove paper review managers,
    so this class inherits from RHConferenceModifBase
    """

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().removePaperReviewManager( ph.getById( id ) )
                    av = ph.getById(id)
                    if av:
                        self._target.revokeModification(av)
                    else:
                        self._target.getAccessController().revokeModificationEmail(id)
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )

#referee classes
class RHConfRefereeBase( RHConfModifReviewingPRMBase ):

    def _checkParams( self, params ):
        RHConfModifReviewingPRMBase._checkParams( self, params )
        if self._conf.getConfPaperReview().getChoice() == CPR.NO_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
            raise MaKaCError("Reviewing mode does not allow creation or deletion of referees")

class RHConfSelectReferee( RHConfRefereeBase ):
    _uh = urlHandlers.UHConfSelectReferee

    def _process( self ):
        p = reviewing.WPConfSelectReferee( self, self._target)
        return p.display( **self._getRequestParams() )

class RHConfAddReferee( RHConfRefereeBase ):

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().addReferee( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )


class RHConfRemoveReferee( RHConfRefereeBase ):

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().removeReferee( ph.getById( id ) )
                    av = ph.getById(id)
                    if av:
                        self._target.revokeModification(av)
                    else:
                        self._target.getAccessController().revokeModificationEmail(id)
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )

#editor classes
class RHConfEditorBase( RHConfModifReviewingPRMBase ):

    def _checkParams( self, params ):
        RHConfModifReviewingPRMBase._checkParams( self, params )
        if self._conf.getConfPaperReview().getChoice() == CPR.NO_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING:
            raise MaKaCError("Reviewing mode does not allow creation or deletion of editors")

class RHConfSelectEditor( RHConfEditorBase ):
    _uh = urlHandlers.UHConfSelectEditor

    def _process( self ):
        p = reviewing.WPConfSelectEditor( self, self._target )
        return p.display( **self._getRequestParams() )

class RHConfAddEditor( RHConfEditorBase ):

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().addEditor( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )


class RHConfRemoveEditor( RHConfEditorBase ):

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().removeEditor( ph.getById( id ) )
                    av = ph.getById(id)
                    if av:
                        self._target.revokeModification(av)
                    else:
                        self._target.getAccessController().revokeModificationEmail(id)
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )

#reviewer classes
class RHConfReviewerBase( RHConfModifReviewingPRMBase ):

    def _checkParams( self, params ):
        RHConfModifReviewingPRMBase._checkParams( self, params )
        if self._conf.getConfPaperReview().getChoice() == CPR.NO_REVIEWING or self._conf.getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
            raise MaKaCError("Reviewing mode does not allow creation or deletion of reviewers")

class RHConfSelectReviewer( RHConfReviewerBase ):
    _uh = urlHandlers.UHConfSelectReviewer

    def _process( self ):
        p = reviewing.WPConfSelectReviewer (self, self._target )
        return p.display( **self._getRequestParams() )

class RHConfAddReviewer( RHConfReviewerBase ):

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().addReviewer( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )


class RHConfRemoveReviewer( RHConfReviewerBase ):

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id is not None and id != '':
                    self._target.getConfPaperReview().removeReviewer( ph.getById( id ) )
                    av = ph.getById(id)
                    if av:
                        self._target.revokeModification(av)
                    else:
                        self._target.getAccessController().revokeModificationEmail(id)
        self._redirect( urlHandlers.UHConfModifReviewingControl.getURL( self._target ) )

