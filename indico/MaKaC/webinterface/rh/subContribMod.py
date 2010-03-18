# -*- coding: utf-8 -*-
##
## $Id: subContribMod.py,v 1.21 2009/06/03 14:36:40 jose Exp $
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.pages.subContributions as subContributions
import MaKaC.conference as conference
import MaKaC.user as user
import MaKaC.domain as domain
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
from MaKaC.common.general import *
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
        p = subContributions.WPSubContributionModification( self, self._target )
        return p.display( **self._getRequestParams() )



#class RHSubContributionPerformModification( RHSubContribModifBase ):
#    _uh = urlHandlers.
#
#    def _process( self ):
#        params = self._getRequestParams()
#        if not ("cancel" in params):
#            self._target.setName( params.get("name", "") )
#            self._target.setDescription( params.get("description", "") )
#        self._redirect( urlHandlers.UHCategoryModification.getURL( self._target ) )


class RHSubContributionTools( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContribModifTools

    def _process( self ):
        p = subContributions.WPSubContributionModifTools( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSubContributionData( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionDataModification

    def _process( self ):
        p = subContributions.WPSubContribData( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSubContributionModifData( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionDataModif

    def _process( self ):
        params = self._getRequestParams()

        self._target.setTitle( params.get("title","") )
        self._target.setDescription( params.get("description","") )
        self._target.setKeywords( params.get("keywords","") )

        self._target.setDuration( params.get("durationHours",""), \
                             params.get("durationMinutes","") )
        self._target.setSpeakerText( params.get("speakers","") )
        self._redirect(urlHandlers.UHSubContributionModification.getURL( self._target ) )

class RHSubContribNewSpeaker( RHSubContribModifBase ):

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
      #  raise '%s'%params
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newSpeaker(self):
        #raise '%s'%self._getRequestParams()
        spk = conference.SubContribParticipation()
        p = self._getRequestParams()
        spk.setTitle(p.get("title",""))
        spk.setFirstName(p.get("name",""))
        spk.setFamilyName(p.get("surName",""))
        spk.setAffiliation(p.get("affiliation",""))
        spk.setEmail(p.get("email",""))
        spk.setAddress(p.get("address",""))
        spk.setPhone(p.get("phone",""))
        spk.setFax(p.get("fax",""))
        self._target.newSpeaker(spk)

    def _process(self):
        params = self._getRequestParams()

        if self._action != "":
            if self._action == "perform":
                self._newSpeaker()
            url=urlHandlers.UHSubContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            p = subContributions.WPSubModNewSpeaker(self, self._target)
            #wf = self.getWebFactory()
            #if wf != None:
            #    p = wf.getSubContributionNewspeaker(self, self._target)
            return p.display(**params)


class RHSubContributionSelectSpeakers( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionSelectSpeakers

    def _process( self ):
        p = subContributions.WPSubContribSelectSpeakers( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSubContributionAddSpeakers( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionAddSpeakers

    def _process( self ):
        params=self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ah=user.AvatarHolder()
            authIndex = self._target.getConference().getAuthorIndex()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                spk = conference.SubContribParticipation()
                if id[:9] == "*author*:":
                    id = id[9:]
                    spk.setDataFromAuthor(authIndex.getById(id)[0])
                else:
                    spk.setDataFromAvatar(ah.getById(id))
                self._target.newSpeaker(spk)
        self._redirect( urlHandlers.UHSubContributionModification.getURL( self._target ) )


class RHSubContributionRemoveSpeakers( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionRemoveSpeakers

    def _checkParams( self, params ):
        RHSubContribModifBase._checkParams( self, params )
        selSpeakers = self._normaliseListParam( params.get( "selAuthor", [] ) )
        self._speakers = []
        for id in selSpeakers:
            self._speakers.append(self._target.getSpeakerById(id) )

    def _process( self ):
        for speaker in self._speakers:
            self._target.removeSpeaker( speaker )
        self._redirect( urlHandlers.UHSubContributionModification.getURL( self._target ) )

class RHEditPresenter( RHSubContribModifBase ):

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        self._authorId=params["authorId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setSpeakerData(self):
        auth=self._target.getSpeakerById(self._authorId)
        p = self._getRequestParams()
        auth.setTitle(p.get("title",""))
        auth.setFirstName(p.get("name",""))
        auth.setFamilyName(p.get("surName",""))
        auth.setAffiliation(p.get("affiliation",""))
        auth.setEmail(p.get("email",""))
        auth.setAddress(p.get("address",""))
        auth.setPhone(p.get("phone",""))
        auth.setFax(p.get("fax",""))

    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setSpeakerData()
            url=urlHandlers.UHSubContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            auth=self._target.getSpeakerById(self._authorId)
            p = subContributions.WPModPresenter(self, self._target)

            params = self._getRequestParams()
            params['author'] = auth

            return p.display(**params)

class RHSubContributionAddMaterial( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionAddMaterial

    def _checkParams( self, params ):
        RHSubContribModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "notype" )
        if typeMat=="notype" or typeMat.strip()=="":
            raise FormValuesError("Please choose a material type")
        self._mf = materialFactories.ContribMFRegistry().getById( typeMat )

    def _process( self ):
        if self._mf:
            if not self._mf.needsCreationPage():
                m = RHSubContributionPerformAddMaterial.create( self._target, self._mf, self._getRequestParams() )
                self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )
                return
        p = subContributions.WPSubContribAddMaterial( self, self._target, self._mf )
        return p.display()


class RHSubContributionPerformAddMaterial( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionPerformAddMaterial

    def _checkParams( self, params ):
        RHSubContribModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        self._mf = materialFactories.ContribMFRegistry().getById( typeMat )

    def create( subContrib, matFactory, matData ):
        if matFactory:
            m = matFactory.create( subContrib )
        else:
            m = conference.Material()
            subContrib.addMaterial( m )
            m.setValues( matData )
        return m
    create = staticmethod( create )

    def _process( self ):
        m = self.create( self._target, self._mf, self._getRequestParams() )
        self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )

class RHMaterialsAdd(RHSubContribModifBase):
    _uh = urlHandlers.UHSubContribModifAddMaterials

    def _checkProtection(self):
        material, _ = self._rhSubmitMaterial._getMaterial()
        if self._target.canUserSubmit(self._aw.getUser()) \
            and (not material or material.getReviewingState() < 3):
            return
        RHSubContribModifBase._checkProtection(self)

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        if not hasattr(self,"_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)

    def _process( self ):
        if self._target.getConference().isClosed():
            p = WPConferenceModificationClosed( self, self._target )
            return p.display()
        r=self._rhSubmitMaterial._process(self, self._getRequestParams())
        if r is None:
            self._redirect(self._uh.getURL(self._target))

        return r


class RHSubContributionRemoveMaterials( RHSubContribModifBase ):
    _uh = urlHandlers.UHSubContributionRemoveMaterials

    def _checkParams( self, params ):
        RHSubContribModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        #self._mf = materialFactories.ConfMFRegistry().getById( typeMat )
        self._materialIds = self._normaliseListParam( params.get("materialId", []) )
        self._returnURL = params.get("returnURL","")

    def _process( self ):
        for id in self._materialIds:
            #Performing the deletion of special material types
            f = materialFactories.ContribMFRegistry().getById( id )
            if f:
                f.remove( self._target )
            else:
                #Performs the deletion of additional material types
                mat = self._target.getMaterialById( id )
                self._target.removeMaterial( mat )
        if self._returnURL != "":
            url = self._returnURL
        else:
            url = urlHandlers.UHSubContribModifMaterials.getURL( self._target )
        self._redirect( url )




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



class RHSubContributionWriteMinutes( RHSubContributionTools ):
    _uh = urlHandlers.UHSubContributionWriteMinutes

    def _checkParams( self, params ):
        RHSubContributionTools._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("OK")
        self._text = params.get("text", "")#.strip()

    def _process( self ):
        params = self._getRequestParams()
        if self._cancel:
            self._redirect( urlHandlers.UHSubContribModifTools.getURL( self._target ) )
        elif self._save:
            #if self._text!="":
                minutes = self._target.getMinutes()
                if not minutes:
                    minutes = self._target.createMinutes()
                minutes.setText( self._text )
                self._redirect( urlHandlers.UHSubContribModifTools.getURL( self._target ) )
        else:
            p = subContributions.WPSubContributionWriteMinutes( self, self._target )
            return p.display(**params)


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


class RHSubContributionReportNumberEdit(RHSubContribModifBase):

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")

    def _process(self):
        params = self._getRequestParams()
        if self._reportNumberSystem!="":
            p=subContributions.WPSubContributionReportNumberEdit(self,self._target, self._reportNumberSystem)
            return p.display(**params)
        else:
            self._redirect(urlHandlers.UHSubContributionModification.getURL( self._target ))

class RHSubContributionReportNumberPerformEdit(RHSubContribModifBase):

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")
        self._reportNumber=params.get("reportNumber","")

    def _process(self):
        if self._reportNumberSystem!="" and self._reportNumber!="":
            self._target.getReportNumberHolder().addReportNumber(self._reportNumberSystem, self._reportNumber)
        self._redirect("%s#reportNumber"%urlHandlers.UHSubContributionModification.getURL( self._target ))


class RHSubContributionReportNumberRemove(RHSubContribModifBase):

    def _checkParams(self, params):
        RHSubContribModifBase._checkParams(self, params)
        self._reportNumberIdsToBeDeleted=self._normaliseListParam( params.get("deleteReportNumber",[]))

    def _process(self):
        nbDeleted = 0
        for id in self._reportNumberIdsToBeDeleted:
            self._target.getReportNumberHolder().removeReportNumberById(int(id)-nbDeleted)
            nbDeleted += 1
        self._redirect("%s#reportNumber"%urlHandlers.UHSubContributionModification.getURL( self._target ))





