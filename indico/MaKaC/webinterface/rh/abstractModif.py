# -*- coding: utf-8 -*-
##
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

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.abstracts as abstracts
import MaKaC.review as review
import MaKaC.user as user
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHAbstractBase, RHConferenceBase
from MaKaC.PDFinterface.conference import ConfManagerAbstractToPDF, ConfManagerAbstractsToPDF
from MaKaC.common.xmlGen import XMLGen
from MaKaC.errors import MaKaCError,ModificationError, FormValuesError
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
from MaKaC.common import Config
import MaKaC.webinterface.common.abstractDataWrapper as abstractDataWrapper
from MaKaC.i18n import _
from MaKaC.webinterface.rh.conferenceModif import CFAEnabled
    
class RCAbstractReviewer(object):
    @staticmethod
    def hasRights(request):
        """ Returns True if the user is an Abstract Reviewer of the given abstract
        """
        #TODO: write this when the ReviewManager for abstracts class is implemented
        return False
    

class RHAbstractModifBase( RHAbstractBase, RHModificationBaseProtected ):
    """ Base class to be used for abstract modification in the admin interface,
        when the request can only be performed by Conference managers.
    """
    
    def _checkParams( self, params ):
        RHAbstractBase._checkParams( self, params )

    def _checkProtection( self ):
        RHModificationBaseProtected._checkProtection( self )
        CFAEnabled.checkEnabled(self)
    
    def _displayCustomPage( self, wf ):
        return None

    def _displayDefaultPage( self ):
        return None

    def _process( self ):
        wf = self.getWebFactory()
        if wf != None:
            res = self._displayCustomPage( wf )
            if res != None:
                return res
        return self._displayDefaultPage()
    

class RHAbstractModifBaseAbstractManager(RHAbstractModifBase):
    """ Base class to be used when the request can only be performed
        by Abstract Managers OR by conference managers
    """
    
    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCAbstractManager
        if not RCAbstractManager.hasRights(self):
            RHAbstractBase._checkProtection(self)
        CFAEnabled.checkEnabled(self)

class RHAbstractModifBaseAbstractReviewer(RHAbstractModifBase):
    """ Base class to be used when the request can only be performed
        by an Abstract Reviewer (and ONLY by an Abstract Reviewer)
    """
    
    def _checkProtection(self):
        if not RCAbstractReviewer.hasRights(self):
            raise MaKaCError("Only the reviewer of this abstract can access this page / perform this request")
        CFAEnabled.checkEnabled(self)
            
class RHRHAbstractModifBaseAbstractReviewingStaff(RHAbstractModifBase):
    """ Base class to be used when the request can only be performed
        by an AM, an AR, OR a Conference Manager
    """
    
    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCAbstractManager
        if not RCAbstractManager.hasRights(self) and not RCAbstractReviewer.hasRights(self):
            RHAbstractBase._checkProtection(self)
        CFAEnabled.checkEnabled(self)


class RHAbstractDelete(RHAbstractModifBase):

    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._remove = params.has_key("confirm")
        self._cancel = params.has_key("cancel")
    
    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHAbstractModTools.getURL( self._abstract) )
        else:
            if self._remove:
                self._conf.getAbstractMgr().removeAbstract(self._target)
                self._redirect( urlHandlers.UHConfAbstractManagment.getURL( self._conf) )
            else:
                p = abstracts.WPModRemConfirmation( self, self._abstract )
                return p.display()
        

class RHAbstractManagment(RHRHAbstractModifBaseAbstractReviewingStaff):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPAbstractManagment( self, self._target )
        return p.display( **self._getRequestParams() )


class RHAbstractSelectSubmitter(RHAbstractModifBase):
    
    def _process( self ):
        p = abstracts.WPAbstractSelectSubmitter( self, self._target )
        return p.display( **self._getRequestParams() )


class RHAbstractSetSubmitter(RHAbstractModifBase):
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            id  = params["selectedPrincipals"]
            self._target.setSubmitter( ph.getById( id ) )
        self._redirect( urlHandlers.UHAbstractManagment.getURL( self._target ) )

class RHAbstractDirectAccess(RHAbstractModifBase, RHConferenceBase):
    
    def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
        RHAbstractModifBase._checkProtection( self )
    
    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self._abstractId = params.get("abstractId","")
        self._abstractExist = False
        try:
            abstract = self._conf.getAbstractMgr().getAbstractById(self._abstractId)
            self._abstractExist = True
            RHAbstractModifBase._checkParams(self, params)
        except KeyError:
            pass
        
    
    def _process( self ):
        if self._abstractExist and self._target is not None:
            p = abstracts.WPAbstractManagment( self, self._target )
            return p.display( **self._getRequestParams() )
        else:
            url = urlHandlers.UHConfAbstractManagment.getURL(self._conf)
            #url.addParam("directAbstractMsg","There is no abstract number %s in this conference"%self._abstractId)
            self._redirect(url)
            return


class RHAbstractToPDF(RHAbstractModifBase):
    
    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "%s - Abstract.pdf"%self._target.getTitle()
        pdf = ConfManagerAbstractToPDF(self._conf, self._target, tz=tz)
        data = pdf.getPDFBin()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractToXML(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        filename = "%s - Abstract.xml"%self._target.getTitle()
        
        x = XMLGen()
        x.openTag("abstract")
        x.writeTag("Id", self._target.getId())
        x.writeTag("Title", self._target.getTitle())
        afm = self._target.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getFields():
            id = f.getId()
            if f.isActive() and self._target.getField(id).strip() != "":
                x.writeTag(id.replace(" ","_"),self._target.getField(id))
        x.writeTag("Conference", self._target.getConference().getTitle())
        l = []
        for au in self._target.getAuthorList():
            if self._target.isPrimaryAuthor(au):
                x.openTag("PrimaryAuthor")
                x.writeTag("FirstName", au.getFirstName())
                x.writeTag("FamilyName", au.getSurName())
                x.writeTag("Email", au.getEmail())
                x.writeTag("Affiliation", au.getAffiliation())
                x.closeTag("PrimaryAuthor")
            else:
                l.append(au)
        
        for au in l:
            x.openTag("Co-Author")
            x.writeTag("FirstName", au.getFirstName())
            x.writeTag("FamilyName", au.getSurName())
            x.writeTag("Email", au.getEmail())
            x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Co-Author") 
        
        for au in self._target.getSpeakerList():
            x.openTag("Speaker")
            x.writeTag("FirstName", au.getFirstName ())
            x.writeTag("FamilyName", au.getSurName())
            x.writeTag("Email", au.getEmail())
            x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Speaker")
        
        #To change for the new contribution type system to:
        #x.writeTag("ContributionType", self._target.getContribType().getName())
        x.writeTag("ContributionType", self._target.getContribType())
        
        for t in self._target.getTrackList():
            x.writeTag("Track", t.getTitle())
        
        x.closeTag("abstract")
        
        data = x.getXml()
        
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class _AbstractWrapper:
    
    def __init__(self,status):
        self._status=status

    def getCurrentStatus(self):
        return self._status
        

class RHAbstractManagmentAccept(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._accept = params.get("accept", None)
        self._warningShown=params.has_key("confirm")
        self._trackId = params.get("track", "")
        self._track=self._conf.getTrackById(params.get("track", ""))
        self._sessionId = params.get("session", "")
        self._session=self._conf.getSessionById(params.get("session", ""))
        self._comments = params.get("comments", "")
        self._typeId = params.get("type", "")
        self._notify=params.has_key("notify")
    
    def _process( self ):
        if self._accept:
            cType=self._conf.getContribTypeById(self._typeId)
            st=review.AbstractStatusAccepted(self._target,None,self._track,cType)
            wrapper=_AbstractWrapper(st)
            tpl=self._target.getOwner().getNotifTplForAbstract(wrapper)
            if self._notify and not self._warningShown and tpl is None:
                p=abstracts.WPModAcceptConfirmation(self,self._target)
                return p.display(track=self._trackId,comments=self._comments,type=self._typeId,session=self._sessionId)
            else:
                self._target.accept(self._getUser(),self._track,cType,self._comments,self._session)
                if self._notify:
                    n=EmailNotificator()
                    self._target.notify(n,self._getUser())
                self._redirect(urlHandlers.UHAbstractManagment.getURL(self._abstract))
        else:
            p = abstracts.WPAbstractManagmentAccept( self, self._target )
            return p.display( **self._getRequestParams() )


class RHAbstractManagmentReject(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._reject = params.get("reject", None)
        self._comments = params.get("comments", "")
        self._notify=params.has_key("notify")
        self._warningShown=params.has_key("confirm")
    
    def _process( self ):
        if self._reject:
            st=review.AbstractStatusRejected(self._target,None,None)
            wrapper=_AbstractWrapper(st)
            tpl=self._target.getOwner().getNotifTplForAbstract(wrapper)
            if self._notify and not self._warningShown and tpl is None:
                p=abstracts.WPModRejectConfirmation(self,self._target)
                return p.display(comments=self._comments)
            else:
                self._target.reject(self._getUser(), self._comments)
                if self._notify:
                    n=EmailNotificator()
                    self._target.notify(n,self._getUser())
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
        else:
            p = abstracts.WPAbstractManagmentReject( self, self._target )
            return p.display( **self._getRequestParams() )


class RHMarkAsDup(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action,self._comments,self._original="","",None
        self._originalId=""
        if params.has_key("OK"):
            self._action="MARK"
            self._comments=params.get("comments","")
            self._originalId=params.get("id","")
            self._original=self._target.getOwner().getAbstractById(self._originalId)

    def _getErrorsInData(self):
        res=[]
        if self._original==None or self._target==self._original:
            res.append( _("invalid original abstract id"))
        return res 
    
    def _process( self ):
        errMsg=""
        if self._action=="MARK":
            errorList=self._getErrorsInData()
            if len(errorList)==0:
                self._target.markAsDuplicated(self._getUser(),self._original,self._comments)
                self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
                return 
            else:
                errMsg="<br>".join(errorList)
        p=abstracts.WPModMarkAsDup(self,self._target)
        return p.display(comments=self._comments,originalId=self._originalId,errorMsg=errMsg)


class RHUnMarkAsDup(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action,self._comments,self._original="","",None
        self._originalId=""
        if params.has_key("OK"):
            self._action="UNMARK"
            self._comments=params.get("comments","")
            
    
    def _process( self ):
        errMsg=""
        if self._action=="UNMARK":
            self._target.unMarkAsDuplicated(self._getUser(),self._comments)
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
            return 
        p=abstracts.WPModUnMarkAsDup(self,self._target)
        return p.display(comments=self._comments,originalId=self._originalId,errorMsg=errMsg)


class RHMergeInto(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action,self._comments,self._targetAbs="","",None
        self._targetAbsId,self._includeAuthors,self._notify="",False,True
        if params.has_key("OK"):
            self._action="MERGE"
            self._comments=params.get("comments","")
            self._targetAbsId=params.get("id","")
            self._includeAuthors=params.has_key("includeAuthors")
            self._notify=params.has_key("notify")
            self._targetAbs=self._target.getOwner().getAbstractById(self._targetAbsId)

    def _getErrorsInData(self):
        res=[]
        if self._targetAbs==None or self._target==self._targetAbs:
            res.append("invalid target abstract id")
        return res 

    def _process( self ):
        errMsg=""
        if self._action=="MERGE":
            errorList=self._getErrorsInData()
            if len(errorList)==0:
                self._target.mergeInto(self._getUser(),self._targetAbs,comments=self._comments,mergeAuthors=self._includeAuthors)
                if self._notify:
                    self._target.notify(EmailNotificator(),self._getUser())
                self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
                return 
            else:
                errMsg="<br>".join(errorList)
        p=abstracts.WPModMergeInto(self,self._target)
        return p.display(comments=self._comments,targetId=self._targetAbsId,errorMsg=errMsg,includeAuthors=self._includeAuthors,notify=self._notify)


class RHUnMerge(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action,self._comments="",""
        if params.has_key("OK"):
            self._action="UNMERGE"
            self._comments=params.get("comments","")
            
    
    def _process( self ):
        if self._action=="UNMERGE":
            self._target.unMerge(self._getUser(),self._comments)
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
            return 
        p=abstracts.WPModUnMerge(self,self._target)
        return p.display(comments=self._comments)


class RHPropToAcc(RHAbstractModifBase):
    
    def _checkProtection(self):
        try:
            RHAbstractModifBase._checkProtection(self)
        except ModificationError,e:
            if self._target.isAllowedToCoordinate(self._getUser()):
                return
            raise e

    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action=""
        if params.has_key("OK"):
            self._action="GO"
            conf=self._target.getConference()
            self._track=conf.getTrackById(params.get("track",""))
            if self._track is None:
                raise FormValuesError( _("You have to choose a track in order to do the proposal. If there are not tracks to select, please change the track assignment of the abstract from its management page"))
            self._contribType=self._conf.getContribTypeById(params.get("contribType",""))
            self._comment=params.get("comment","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
    
    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if self._action=="GO":
            self._abstract.proposeToAccept(self._getUser(),\
                self._track,self._contribType,self._comment)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=abstracts.WPModPropToAcc(self,self._target)
            return p.display()


class RHPropToRej(RHAbstractModifBase):
    
    def _checkProtection(self):
        try:
            RHAbstractModifBase._checkProtection(self)
        except ModificationError,e:
            if self._target.isAllowedToCoordinate(self._getUser()):
                return
            raise e
    
    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams( self, params )
        self._action=""
        if params.has_key("OK"):
            self._action="GO"
            conf=self._target.getConference()
            self._track=conf.getTrackById(params.get("track",""))
            if self._track is None:
                raise FormValuesError( _("You have to choose a track in order to do the proposal. If there are not tracks to select, please change the track assignment of the abstract from its management page"))
            self._contribType=self._conf.getContribTypeById(params.get("contribType",""))
            self._comment=params.get("comment","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
    
    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if self._action=="GO":
            self._abstract.proposeToReject(self._getUser(),\
                self._track,self._comment)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=abstracts.WPModPropToRej(self,self._target)
            return p.display()


class RHWithdraw(RHAbstractModifBase):
    
    def _checkParams(self,params):
        RHAbstractModifBase._checkParams(self,params)
        self._action,self._comments="",""
        if params.has_key("OK"):
            self._action="WITHDRAW"
            self._comment=params.get("comment","")
        if params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if self._action=="WITHDRAW":
            self._target.withdraw(self._getUser(),self._comment)
            self._redirect(url)
            return 
        elif self._action=="CANCEL":
            self._redirect(url)
            return 
        else:
            p=abstracts.WPModWithdraw(self,self._target)
            return p.display()

class RHBackToSubmitted(RHAbstractModifBase):
    
    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if isinstance(self._abstract.getCurrentStatus(), review.AbstractStatusWithdrawn):
            self._abstract.setCurrentStatus(review.AbstractStatusSubmitted(self._abstract))
        self._redirect(url)


class RHAbstractManagmentChangeTrack(RHAbstractModifBase):
    
    def _checkParams( self, params ):
        self._cancel = params.get("cancel", None)
        self._save = params.get("save", None)
        self._tracks = self._normaliseListParam(params.get("tracks", []))
        RHAbstractModifBase._checkParams( self, params )
    
    def _process( self ):
        if self._save:
            tracks = []
            for trackId in self._tracks:
                tracks.append( self._conf.getTrackById(trackId) )
            self._target.setTracks( tracks )
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
        elif self._cancel:
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
        else:
            p = abstracts.WPAbstractManagmentChangeTrack( self, self._target )
            return p.display( **self._getRequestParams() )


class RHAbstractTrackManagment(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPAbstractTrackManagment( self, self._target )
        return p.display( **self._getRequestParams() )


class RHAC(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPModAC(self,self._target)
        return p.display()


class RHEditData(RHAbstractModifBase):

    def _getDirectionKey(self, params):
        for key in params.keys():
            if key.startswith("upPA"):
                return key.split("_")
            elif key.startswith("downPA"):
                return key.split("_")
            elif key.startswith("upCA"):
                return key.split("_")
            elif key.startswith("downCA"):
                return key.split("_")
        return None
    
    def _checkParams(self,params):
        RHAbstractModifBase._checkParams(self,params)
        toNorm=["auth_prim_id","auth_prim_title", "auth_prim_first_name",
            "auth_prim_family_name","auth_prim_affiliation", 
            "auth_prim_email", "auth_prim_phone", "auth_prim_speaker",
            "auth_co_id","auth_co_title", "auth_co_first_name",
            "auth_co_family_name","auth_co_affiliation", 
            "auth_co_email", "auth_co_phone", "auth_co_speaker"]
        for k in toNorm:
            params[k]=self._normaliseListParam(params.get(k,[]))
        self._abstractData=abstractDataWrapper.Abstract(self._conf.getAbstractMgr().getAbstractFieldsMgr(), **params)
        self._action=""
        if params.has_key("OK"):
            self._action="UPDATE"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("addPrimAuthor"):
            self._abstractData.newPrimaryAuthor()
        elif params.has_key("addCoAuthor"):
            self._abstractData.newCoAuthor()
        elif params.has_key("remPrimAuthors"):
            idList=self._normaliseListParam(params.get("sel_prim_author",[]))
            self._abstractData.removePrimaryAuthors(idList)
        elif params.has_key("remCoAuthors"):
            idList=self._normaliseListParam(params.get("sel_co_author",[]))
            self._abstractData.removeCoAuthors(idList)
        else:
            arrowKey = self._getDirectionKey(params)
            if arrowKey != None:
                id = arrowKey[1]
                if arrowKey[0] == "upPA":
                    self._abstractData.upPrimaryAuthors(id)
                elif arrowKey[0] == "downPA":
                    self._abstractData.downPrimaryAuthors(id)
                elif arrowKey[0] == "upCA":
                    self._abstractData.upCoAuthors(id)
                elif arrowKey[0] == "downCA":
                    self._abstractData.downCoAuthors(id)
            else:
                self._abstractData=abstractDataWrapper.Abstract(self._conf.getAbstractMgr().getAbstractFieldsMgr())
                self._abstractData.mapAbstract(self._target)
    
    def _process( self ):
        if self._action=="UPDATE":
            if not self._abstractData.hasErrors():
                self._abstractData.updateAbstract(self._target)
                self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
                return
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
            return
        p = abstracts.WPModEditData(self,self._target,self._abstractData)
        return p.display()


class RHIntComments(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPModIntComments(self,self._target)
        return p.display()


class RHNewIntComment(RHIntComments):
    
    def _checkParams(self,params):
        RHIntComments._checkParams(self,params)
        self._action=""
        if params.has_key("OK"):
            self._action="UPDATE"
            self._content=params.get("content","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
    
    def _process( self ):
        if self._action=="UPDATE":
            c=review.Comment(self._getUser())
            c.setContent(self._content)
            self._target.addIntComment(c)
            self._redirect(urlHandlers.UHAbstractModIntComments.getURL(self._target))
            return 
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHAbstractModIntComments.getURL(self._target))
            return
        p = abstracts.WPModNewIntComment(self,self._target)
        return p.display()


class RHIntCommentBase(RHAbstractModifBase):
    
    def _checkParams(self,params):
        RHAbstractModifBase._checkParams(self,params)
        id=params.get("intCommentId","")
        if id=="":
            raise MaKaCError( _("the internal comment identifier hasn't been specified"))
        abstract=self._target
        self._target=abstract.getIntCommentById(id)
        

class RHIntCommentRem(RHIntCommentBase):
    
    def _process(self):
        abstract=self._target.getAbstract()
        abstract.removeIntComment(self._target)
        self._redirect(urlHandlers.UHAbstractModIntComments.getURL(abstract))
    

class RHIntCommentEdit(RHIntCommentBase):
    
    def _checkParams(self,params):
        RHIntCommentBase._checkParams(self,params)
        self._action=""
        if params.has_key("OK"):
            self._action="UPDATE"
            self._content=params.get("content","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        
    def _process(self):
        if self._action=="UPDATE":
            self._target.setContent(self._content)
            self._redirect(urlHandlers.UHAbstractModIntComments.getURL(self._target.getAbstract()))
            return
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHAbstractModIntComments.getURL(self._target.getAbstract()))
            return 
        p=abstracts.WPModIntCommentEdit(self,self._target)
        return p.display()


class RHNotifLog(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPModNotifLog(self,self._target)
        return p.display()

class RHTools(RHAbstractModifBase):
    
    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHAbstractModifBase._checkProtection( self )
    
    def _process( self ):
        p = abstracts.WPModTools(self,self._target)
        return p.display()





