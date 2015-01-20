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

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.conference as conference
import MaKaC.user as user
import MaKaC.domain as domain
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
from MaKaC.errors import FormValuesError
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed

class RHSubContribModifBase( RHModificationBaseProtected ):

    def _checkProtection( self ):
        owner=self._target.getContribution()
        if owner.getSession() != None:
            if owner.getSession().canCoordinate(self.getAW(), "modifContribs"):
                return
        RHModificationBaseProtected._checkProtection( self )

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setSubContribution( params )
        self._target = l.getObject()
        self._conf = self._target.getConference()
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def getWebFactory( self ):
        wr = webFactoryRegistry.WebFactoryRegistry()
        self._wf = wr.getFactory( self._target.getConference())
        return self._wf


class RHSubContributionModification( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionModification

    def _process( self ):
        if self._target.getOwner().getOwner().isClosed():
            p = subContributions.WPSubContributionModificationClosed(self, self._target)
        else:
            p = subContributions.WPSubContributionModification( self, self._target )
        return p.display( **self._getRequestParams() )

class RHSubContributionTools( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContribModifTools

    def _process( self ):
        if self._target.getOwner().getOwner().isClosed():
            p = subContributions.WPSubContributionModificationClosed(self, self._target)
        else:
            p = subContributions.WPSubContributionModifTools( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSubContributionData( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionDataModification

    def _process( self ):
        if self._target.getOwner().getOwner().isClosed():
            p = subContributions.WPSubContributionModificationClosed(self, self._target)
        else:
            p = subContributions.WPSubContribData( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSubContributionModifData( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionDataModif

    def _process( self ):
        params = self._getRequestParams()

        self._target.setTitle( params.get("title","") )
        self._target.setDescription( params.get("description","") )
        self._target.setKeywords( params.get("keywords","") )
        try:
            durationHours = int(params.get("durationHours",""))
        except ValueError:
            raise FormValuesError(_("Please specify a valid hour format (0-23)."))
        try:
            durationMinutes = int(params.get("durationMinutes",""))
        except ValueError:
            raise FormValuesError(_("Please specify a valid minutes format (0-59)."))

        self._target.setDuration( durationHours, durationMinutes )
        self._target.setSpeakerText( params.get("speakers","") )
        self._redirect(urlHandlers.UHSubContributionModification.getURL( self._target ) )



class RHMaterialsAdd(RHSubmitMaterialBase, RHSubContribModifBase):
    _uh = urlHandlers.UHSubContribModifAddMaterials

    def _checkProtection(self):
        material, _ = self._getMaterial(forceCreate = False)
        if self._target.canUserSubmit(self._aw.getUser()) \
            and (not material or material.getReviewingState() < 3):
            self._loggedIn = True
            return
        RHSubmitMaterialBase._checkProtection(self)

    def __init__(self, req):
        RHSubContribModifBase.__init__(self, req)
        RHSubmitMaterialBase.__init__(self)

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        RHSubmitMaterialBase._checkParams(self, params)


class RHSubContributionDeletion( RHSubContributionTools ):
    _uh = urlHandlers.UHSubContributionDelete

    def _checkParams( self, params ):
        RHSubContributionTools._checkParams( self, params )
        self._cancel = False
        if "cancel" in params:
            self._cancel = True
        self._confirmation = params.has_key("confirm")

    def _perform( self ):
        self._target.getOwner().removeSubContribution(self._target)

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHSubContribModifTools.getURL( self._target ) )
        elif self._confirmation:
            owner = self._target.getOwner()
            self._perform()

            self._redirect( urlHandlers.UHContributionModification.getURL( owner ) )
        else:
            p = subContributions.WPSubContributionDeletion( self, self._target )
            return p.display(**self._getRequestParams())


class RHMaterials(RHSubContribModifBase):
    _uh = urlHandlers.UHSubContribModifMaterials

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        #if not hasattr(self, "_rhSubmitMaterial"):
        #    self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        #self._rhSubmitMaterial._checkParams(params)

    def _process( self ):
        if self._target.getOwner().getOwner().isClosed():
            p = subContributions.WPSubContributionModificationClosed( self, self._target )
            return p.display()

        p = subContributions.WPSubContributionModifMaterials( self, self._target )
        return p.display(**self._getRequestParams())

