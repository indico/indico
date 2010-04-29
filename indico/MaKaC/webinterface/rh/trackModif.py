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

from sets import Set

from BTrees.OOBTree import OOBTree

import MaKaC.webinterface.pages.tracks as tracks
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.user as user
import MaKaC.webinterface.common.abstractFilters as abstractFilters
import MaKaC.review as review
from MaKaC.webinterface.rh.conferenceBase import RHTrackBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.errors import MaKaCError
from MaKaC.PDFinterface.conference import TrackManagerAbstractToPDF, TrackManagerAbstractsToPDF
from MaKaC.common import Config
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.PDFinterface.conference import ConfManagerContribsToPDF
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.i18n import _


class RHTrackModifBase( RHTrackBase, RHModificationBaseProtected ):
    
    def _checkParams( self, params ):
        RHTrackBase._checkParams( self, params )

    def _checkProtection( self ):
        RHModificationBaseProtected._checkProtection( self )
    

class RHTrackModification( RHTrackModifBase ):

    def _process( self ):
        p = tracks.WPTrackModification( self, self._track )
        return p.display()


class RHTrackDataModification( RHTrackModifBase ):

    def _process( self ):
        p = tracks.WPTrackDataModification( self, self._track )
        return p.display()


class RHTrackPerformDataModification(RHTrackModifBase):

    def _checkParams(self,params):
        RHTrackModifBase._checkParams(self,params)
        self._cancel=params.has_key("cancel")
    
    def _process(self):
        if self._cancel:
            self._redirect(urlHandlers.UHTrackModification.getURL(self._track))
        else:
            params=self._getRequestParams()
            self._track.setTitle(params["title"])
            self._track.setDescription(params["description"])
            self._track.setCode(params["code"])
            self._redirect(urlHandlers.UHTrackModification.getURL(self._track))


class RHTrackCoordination( RHTrackModifBase ):
    
    def _checkProtection(self):
        RHTrackModifBase._checkProtection(self)
        if not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("You cannot access this option because \"Call for abstracts\" was disabled"))
    
    def _process( self ):
        p = tracks.WPTrackModifCoordination( self, self._track )
        return p.display()


class RHTrackSelectCoordinators( RHTrackCoordination ):
    
    def _process( self ):
        p = tracks.WPTrackModifSelectCoordinators( self, self._track )
        return p.display( **self._getRequestParams() )


class RHTrackAddCoordinators( RHTrackCoordination ):
    
    def _checkParams( self, params ):
        RHTrackCoordination._checkParams( self, params )
        selIds = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        ah = user.AvatarHolder()
        self._coordinators = []
        for id in selIds:
            av = ah.getById( id )
            if av is not None:
                self._coordinators.append( av )
    
    def _process( self ):
        for av in self._coordinators:
            self._track.addCoordinator( av )
        self._redirect( urlHandlers.UHTrackModifCoordination.getURL( self._track ) )

    
class RHTrackRemoveCoordinators( RHTrackCoordination ):
    
    def _checkParams( self, params ):
        RHTrackCoordination._checkParams( self, params )
        selIds = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        ah = user.AvatarHolder()
        self._coordinators = []
        for id in selIds:
            self._coordinators.append( ah.getById( id ) )
    
    def _process( self ):
        for av in self._coordinators:
            self._track.removeCoordinator( av )
        self._redirect( urlHandlers.UHTrackModifCoordination.getURL( self._track ) )


class TrackCoordinationError( MaKaCError ):
    pass 
    

class RHTrackAbstractsBase( RHTrackModifBase ):
    """Base class for the areas accessible with track coordination privileges.
    """

    def _checkProtection( self, checkCFADisabled=True ):
        """
        """
        if not self._target.canCoordinate( self.getAW() ):
            if self._getUser() == None:
                self._checkSessionUser()
            else:
                raise TrackCoordinationError("You don't have rights to coordinate this track")
        if checkCFADisabled and not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("You cannot access this option because \"Call for abstracts\" was disabled"))

class _TrackAbstractFilterField( filters.FilterField ):
    
    def __init__( self, track, values, showNoValue=True ):
        self._track = track
        filters.FilterField.__init__(self,track.getConference(),values,showNoValue)


class _StatusFilterField( _TrackAbstractFilterField ):
    """
    """
    _id = "status"

    def satisfies( self, abstract ):
        """
        """
        s = tracks.AbstractStatusTrackViewFactory().getStatus( self._track, abstract )
        return s.getId() in self.getValues()


class _ContribTypeFilterField( _TrackAbstractFilterField, abstractFilters.ContribTypeFilterField ):
    """
    """
    _id = "type"

    def __init__( self, track, values, showNoValue=True ):
        _TrackAbstractFilterField.__init__( self, track, values, showNoValue )
    
    def satisfies( self, abstract ):
        """
        """
        return abstractFilters.ContribTypeFilterField.satisfies(self, abstract)


class _MultipleTrackFilterField(_TrackAbstractFilterField):
    _id = "multiple_tracks"
    
    def satisfies( self, abstract ):
        return len( abstract.getTrackList() )>1


class _CommentsTrackFilterField(_TrackAbstractFilterField, abstractFilters.CommentFilterField):
    _id = "comment"

    def __init__( self, track, values, showNoValue=True ):
        _TrackAbstractFilterField.__init__( self, track, values, showNoValue )
    
    def satisfies( self, abstract ):
        """
        """
        return abstractFilters.CommentFilterField.satisfies(self, abstract)


class _AccContribTypeFilterField(_TrackAbstractFilterField,abstractFilters.AccContribTypeFilterField):
    """
    """
    _id = "acc_type"

    def __init__(self,track,values,showNoValue=True):
        _TrackAbstractFilterField.__init__(self,track,values,showNoValue)
    
    def satisfies(self,abstract):
        astv = tracks.AbstractStatusTrackViewFactory().getStatus( self._track, abstract )
        if astv.__class__ in [tracks._ASTrackViewAccepted,\
                            tracks._ASTrackViewPA]:
            if astv.getContribType() is None or astv.getContribType()=="":
                return self._showNoValue
            return astv.getContribType() in self._values
        else:
            return self._showNoValue

class TrackAbstractsFilterCrit(filters.FilterCriteria):
    _availableFields = { \
                _ContribTypeFilterField.getId():  _ContribTypeFilterField, \
                _StatusFilterField.getId(): _StatusFilterField, \
                _MultipleTrackFilterField.getId(): _MultipleTrackFilterField, \
                _CommentsTrackFilterField.getId(): _CommentsTrackFilterField,
                _AccContribTypeFilterField.getId(): _AccContribTypeFilterField }

    def __init__(self,track,crit={}):
        self._track = track
        filters.FilterCriteria.__init__(self,track.getConference(),crit)

    def _createField(self,klass,values ):
        return klass(self._track,values)

    def satisfies( self, abstract ):
        for field in self._fields.values():
            if not field.satisfies( abstract ):
                return False
        return True


class _TrackAbstractsSortingField( filters.SortingField ):
    
    def __init__( self, track ):
        self._track = track
        filters.SortingField.__init__( self )


class _ContribTypeSF( _TrackAbstractsSortingField, abstractFilters.ContribTypeSortingField ):
    
    _id = "type"

    def __init__( self, track ):
        _TrackAbstractsSortingField.__init__( self, track )

    def compare( self, a1, a2 ):
        return abstractFilters.ContribTypeSortingField.compare( self, a1, a2 )


class _StatusSF( _TrackAbstractsSortingField ):
    _id = "status"

    def compare( self, a1, a2 ):
        statusA1 = tracks.AbstractStatusTrackViewFactory().getStatus( self._track, a1 )
        statusA2 = tracks.AbstractStatusTrackViewFactory().getStatus( self._track, a2 )
        return cmp( statusA1.getLabel(), statusA2.getLabel() )

class _NumberSF( _TrackAbstractsSortingField ):
    _id = "number"

    def compare( self, a1, a2 ):
        try:
            a = int(a1.getId())
            b = int(a2.getId())
        except:
            a = a1.getId()
            b = a2.getId()
        return cmp( a, b )


class _DateSF( _TrackAbstractsSortingField ):
    _id = "date"

    def compare( self, a1, a2 ):
        
        return cmp( a2.getSubmissionDate(), a1.getSubmissionDate() )


class TrackAbstractsSortingCrit( filters.SortingCriteria ):
    """
    """
    _availableFields = { _ContribTypeSF.getId(): _ContribTypeSF, \
                        _StatusSF.getId(): _StatusSF, \
                        _NumberSF.getId(): _NumberSF, \
                        _DateSF.getId(): _DateSF }

    
    def __init__( self, track, crit=[] ):
        """
        """
        self._track = track
        filters.SortingCriteria.__init__( self, crit )

    def _createField( self, fieldKlass ):
        """
        """
        return fieldKlass( self._track )


class RHTrackAbstractList( RHTrackAbstractsBase ):

    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams( self, params )
        filterUsed = params.has_key( "OK" ) #this variable is true when the 
                                            #   filter has been used
        filter = {}
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append(type)
        else:
            for id in self._normaliseListParam(params.get("selTypes",[])):
                ltypes.append(self._conf.getContribTypeById(id))
        filter["type"]=ltypes
        lstatus=[]
        if not filterUsed:
            sl = tracks.AbstractStatusTrackViewFactory().getStatusList()
            for statusKlass in sl:
                lstatus.append( statusKlass.getId() )
            pass
        filter["status"] = self._normaliseListParam( params.get("selStatus", lstatus) )
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append( type )
        else:
            for id in self._normaliseListParam(params.get("selAccTypes",[])):
                ltypes.append(self._conf.getContribTypeById(id))
        filter["acc_type"]=ltypes
        if params.has_key("selMultipleTracks"):
            filter["multiple_tracks"] = ""
        if params.has_key("selOnlyComment"):
            filter["comment"] = ""
        self._criteria = TrackAbstractsFilterCrit( self._track, filter )
        typeShowNoValue,accTypeShowNoValue=True,True
        if filterUsed:
            typeShowNoValue =  params.has_key("typeShowNoValue")
            accTypeShowNoValue= params.has_key("accTypeShowNoValue")
        self._criteria.getField("type").setShowNoValue( typeShowNoValue )
        self._criteria.getField("acc_type").setShowNoValue(accTypeShowNoValue)
        self._sortingCrit = TrackAbstractsSortingCrit( self._track, [params.get( "sortBy", "number").strip()] )
        self._selectAll = params.get("selectAll", None)
        self._msg = params.get("directAbstractMsg","")
        
    
    def _process( self ):
        p = tracks.WPTrackModifAbstracts( self, self._track, self._msg )
        return p.display( filterCrit= self._criteria, \
                            sortingCrit = self._sortingCrit, \
                            selectAll = self._selectAll )


class RHTrackAbstractBase( RHTrackAbstractsBase ):
    
    def _checkParams( self, params ):
        RHTrackModifBase._checkParams( self, params )
        absId = params.get( "abstractId", "" ).strip()
        if absId == "":
            raise MaKaCError( _("Abstract identifier not specified"))
        self._abstract = self._track.getAbstractById( absId )


class RHTrackAbstract( RHTrackAbstractBase ):
    
    def _process( self ):
        p = tracks.WPTrackAbstractModif( self, self._track, self._abstract )
        return p.display()


class RHTrackAbstractDirectAccess( RHTrackAbstractBase ):
    
    def _checkParams(self, params):
        self._params = params
        RHTrackBase._checkParams(self, params)
        self._abstractId = params.get("abstractId","")
        self._abstractExist = False
        try:
            abstract = self._track.getAbstractById(self._abstractId)
            self._abstractExist = True
            RHTrackAbstractBase._checkParams(self, params)
        except KeyError:
            pass
    
    def _process( self ):
        if self._abstractExist:
            p = tracks.WPTrackAbstractModif( self, self._track, self._abstract )
            return p.display()
        else:
            url = urlHandlers.UHTrackModifAbstracts.getURL(self._track)
            #url.addParam("directAbstractMsg","There is no abstract number %s in this track"%self._abstractId)
            self._redirect(url)
            return


class RHTrackAbstractPropToAccept( RHTrackAbstractBase ):
    
    def _checkParams(self,params):
        RHTrackAbstractBase._checkParams(self,params)
        self._action=""
        self._comment=params.get("comment","")
        self._contribType=params.get("contribType",self._abstract.getContribType())
        if params.has_key("OK"):
            self._action = "GO"
            ctId = ""
            if self._abstract.getContribType():
                ctId=self._abstract.getContribType().getId()
            ctId=params.get("contribType",ctId)
            self._contribType=self._abstract.getConference().getContribTypeById(ctId)
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process( self ):
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract )
        if self._action == "CANCEL":
            self._redirect( url )
        elif self._action == "GO":
            r = self._getUser()
            self._abstract.proposeToAccept( r, self._track, self._contribType, self._comment )
            self._redirect( url )
        else:
            p=tracks.WPTrackAbstractPropToAcc(self,self._track,self._abstract)
            return p.display(contribType=self._contribType,\
                                comment=self._comment)


class RHTrackAbstractPropToReject( RHTrackAbstractBase ):
    
    def _checkParams( self, params ):
        RHTrackAbstractBase._checkParams( self, params )
        self._action, self._comment = "", ""
        if params.has_key("OK"):
            self._action = "GO"
            self._comment = params.get("comment", "")
        elif params.has_key("CANCEL"):
            self._action = "CANCEL"

    def _process( self ):
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract )
        if self._action == "CANCEL":
            self._redirect( url )
        elif self._action == "GO":
            r = self._getUser()
            self._abstract.proposeToReject( r, self._track, self._comment )
            self._redirect( url )
        else:
            p = tracks.WPTrackAbstractPropToRej( self, self._track, self._abstract )
            return p.display()


class RHTrackAbstractPropForOtherTracks( RHTrackAbstractBase ):
    
    def _checkParams( self, params ):
        RHTrackAbstractBase._checkParams( self, params )
        self._action, self._comment = "", ""
        if params.has_key("OK"):
            self._action = "GO"
            self._comment = params.get("comment", "")
            self._propTracks = []
            for trackId in self._normaliseListParam( params.get("selTracks", []) ):
                self._propTracks.append( self._conf.getTrackById(trackId) )
        elif params.has_key("CANCEL"):
            self._action = "CANCEL"

    def _process( self ):
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract )
        if self._action == "CANCEL":
            self._redirect( url )
        elif self._action == "GO":
            if self._propTracks != []:
                r = self._getUser()
                self._abstract.proposeForOtherTracks( r, self._track, self._comment, self._propTracks )
            self._redirect( url )
        else:
            p = tracks.WPAbstractPropForOtherTracks( self, self._track, self._abstract )
            return p.display()


class RHModAbstractMarkAsDup(RHTrackAbstractBase):
    
    def _checkParams( self, params ):
        RHTrackAbstractBase._checkParams( self, params )
        self._action,self._comments,self._original="","",None
        self._originalId=""
        if params.has_key("OK"):
            self._action="MARK"
            self._comments=params.get("comments","")
            self._originalId=params.get("id","")
            self._original=self._abstract.getOwner().getAbstractById(self._originalId)

    def _getErrorsInData(self):
        res=[]
        if self._original==None or self._target==self._original:
            res.append("invalid original abstract id")
        return res 
    
    def _process( self ):
        errMsg=""
        if self._action=="MARK":
            errorList=self._getErrorsInData()
            if len(errorList)==0:
                self._abstract.markAsDuplicated(self._getUser(),self._original,self._comments, self._track)
                self._redirect(urlHandlers.UHTrackAbstractModif.getURL(self._track,self._abstract))
                return 
            else:
                errMsg="<br>".join(errorList)
        p=tracks.WPModAbstractMarkAsDup(self,self._track,self._abstract)
        return p.display(comments=self._comments,originalId=self._originalId,errorMsg=errMsg)


class RHModAbstractUnMarkAsDup(RHTrackAbstractBase):
    
    def _checkParams( self, params ):
        RHTrackAbstractBase._checkParams( self, params )
        self._action,self._comments="",""
        if params.has_key("OK"):
            self._action="UNMARK"
            self._comments=params.get("comments","")
            
    
    def _process( self ):
        if self._action=="UNMARK":
            self._abstract.unMarkAsDuplicated(self._getUser(),self._comments, self._track)
            self._redirect(urlHandlers.UHTrackAbstractModif.getURL(self._track,self._abstract))
            return 
        p = tracks.WPModAbstractUnMarkAsDup(self,self._track,self._abstract)
        return p.display(comments=self._comments)

class RHAbstractToPDF(RHTrackAbstractBase):
    
    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "%s - Abstract.pdf"%self._target.getTitle()
        pdf = TrackManagerAbstractToPDF(self._conf, self._abstract, self._track, tz=tz)
        data = pdf.getPDFBin()
        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        self._req = req
    
    def _checkParams( self, params ):
        self._pdf = params.get("PDF", None)
        self._mail = params.get("mail", None)
        self._participant = params.get("PART", None)
        self._tplPreview = params.get("tplPreview", None)
        self._params = params
        
    
    def _process( self ):
        if self._pdf:
            return RHAbstractsToPDF(self._req).process( self._params )
        elif self._mail:
            return RHAbstractSendNotificationMail(self._req).process( self._params )
        elif self._tplPreview:
            return RHAbstractTPLPreview(self._req).process( self._params )
        elif self._participant:
            return RHAbstractsParticipantList(self._req).process( self._params )
        else:
            return "no action to do"
    
    def process(self, params):
        self._checkParams(params)
        ret = self._process()
        if not ret:
            return "None"
        return ret


class RHAbstractTPLPreview(RHTrackBase):
    
    def _checkParams(self, params):
        RHTrackBase._checkParams( self, params )
        self._notifTplId = params.get("notifTpl","")
    
    def _process(self):
        tpl = self._conf.getAbstractMgr().getNotificationTplById(self._notifTplId)
        self._redirect(urlHandlers.UHAbstractModNotifTplPreview.getURL(tpl))
    
    

class AbstractNotification:
    
    def __init__(self, conf, abstract):
        self._conf = conf
        self._abstract = abstract
    
    def getDict(self):
        dict = {}
        dict["conference_title"] = self._conf.getTitle()
        dict["conference_URL"] = str(urlHandlers.UHConferenceDisplay.getURL(self._conf))
        dict["abstract_title"] = self._abstract.getTitle()
        dict["abstract_track"] = "No track attributed"
        dict["contribution_type"] = "No type defined"
        if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusAccepted:
            dict["abstract_track"] = self._abstract.getCurrentStatus().getTrack().getTitle()
            dict["contribution_type"] = self._abstract.getContribType()#.getName()
        dict["submitter_first_name"] = self._abstract.getSubmitter().getFirstName()
        dict["submitter_familly_name"] = self._abstract.getSubmitter().getSurName()
        dict["submitter_title"] = self._abstract.getSubmitter().getTitle()
        dict["abstract_URL"] = str(urlHandlers.UHAbstractDisplay.getURL(self._abstract))
        return dict


class RHAbstractSendNotificationMail(RHTrackModification):
    
    def _checkParams( self, params ):
        RHTrackModification._checkParams( self, params )
        notifTplId = params.get("notifTpl", "")
        self._notifTpl = self._conf.getAbstractMgr().getNotificationTplById(notifTplId)
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        abMgr = self._conf.getAbstractMgr()
        for id in self._abstractIds:
            self._abstracts.append(abMgr.getAbstractById(id))
    
    def _process( self ):
        count = 0
        for abstract in self._abstracts:
            dict = AbstractNotification(self._conf, abstract).getDict()
            s = self._notifTpl.getTplSubject()
            b = self._notifTpl.getTplBody()
            maildata = { "fromAddr": self._notifTpl.getFromAddr(), "toList": [abstract.getSubmitter().getEmail()], "subject": s%dict, "body": text }
            GenericMailer.send(GenericNotification(maildata))
            self._conf.newSentMail(abstract.getSubmitter(), mail.getSubject(), b%dict)
            count += 1
            
        #self._redirect(urlHandlers.UHConfAbstractManagment.getURL(self._conf))
        
        p = conferences.WPAbstractSendNotificationMail(self, self._conf, count )
        return p.display()


class RHAbstractsToPDF(RHTrackAbstractsBase):
    
    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams( self, params )
        self._abstractIds = self._normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        abMgr = self._conf.getAbstractMgr()
        for id in self._abstractIds:
            if abMgr.getAbstractById(id).canView(self._aw):
                self._abstracts.append(abMgr.getAbstractById(id))

    
    def _process( self ): 
        tz = self._conf.getTimezone()
        filename = "Abstracts.pdf"
        if not self._abstracts:
            return "No abstract to print"
        pdf = TrackManagerAbstractsToPDF(self._conf, self._track, self._abstracts,tz=tz)
        data = pdf.getPDFBin()
        self._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s; name="%s\""""%(mimetype, filename )
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractIntComments( RHTrackAbstractBase ):
    
    def _process( self ):
        p = tracks.WPModAbstractIntComments(self,self._track,self._abstract)
        return p.display()


class RHAbstractIntCommentNew(RHAbstractIntComments):
    
    def _checkParams(self,params):
        RHAbstractIntComments._checkParams(self,params)
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
            self._abstract.addIntComment(c)
            self._redirect(urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
            return 
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
            return
        p = tracks.WPModAbstractIntCommentNew(self,self._track,self._abstract)
        return p.display()


class RHAbstractIntCommentBase(RHTrackAbstractBase):
    
    def _checkParams(self,params):
        RHTrackAbstractBase._checkParams(self,params)
        id=params.get("intCommentId","")
        if id=="":
            raise MaKaCError( _("the internal comment identifier hasn't been specified"))
        self._comment=self._abstract.getIntCommentById(id)
        

class RHAbstractIntCommentRem(RHAbstractIntCommentBase):
    
    def _process(self):
        self._abstract.removeIntComment(self._comment)
        self._redirect(urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
    

class RHAbstractIntCommentEdit(RHAbstractIntCommentBase):
    
    def _checkParams(self,params):
        RHAbstractIntCommentBase._checkParams(self,params)
        self._action=""
        if params.has_key("OK"):
            self._action="UPDATE"
            self._content=params.get("content","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        
    def _process(self):
        if self._action=="UPDATE":
            self._comment.setContent(self._content)
            self._redirect(urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
            return
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHTrackAbstractModIntComments.getURL(self._track,self._abstract))
            return 
        p=tracks.WPModAbstractIntCommentEdit(self,self._track,self._comment)
        return p.display()


class RHAbstractsParticipantList(RHTrackAbstractsBase):
                
    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams( self, params )
        self._abstractIds = self._normaliseListParam( params.get("abstracts", []) )
        self._displayedGroups = params.get("displayedGroups", [])
        if type(self._displayedGroups) != list:
            self._displayedGroups = [self._displayedGroups]
        self._clickedGroup = params.get("clickedGroup","")

    def _setGroupsToDisplay(self):
        if self._clickedGroup in self._displayedGroups:
            self._displayedGroups.remove(self._clickedGroup)
        else:
            self._displayedGroups.append(self._clickedGroup)
        
    def _process( self ):
        if not self._abstractIds:
            return "<table align=\"center\" width=\"100%%\"><tr><td>There are no abstracts</td></tr></table>"
        
        submitters = OOBTree()
        primaryAuthors = OOBTree()
        coAuthors = OOBTree()
        submitterEmails = Set()
        primaryAuthorEmails = Set()
        coAuthorEmails = Set()

        self._setGroupsToDisplay()
        
        abMgr = self._conf.getAbstractMgr()
        for abstId in self._abstractIds:
            abst = abMgr.getAbstractById(abstId)
            #Submitters
            subm = abst.getSubmitter()
            keySB = "%s-%s-%s"%(subm.getSurName().lower(), subm.getFirstName().lower(), subm.getEmail().lower())
            submitters[keySB] = subm
            submitterEmails.add(subm.getEmail())
            #Primary authors
            for pAut in abst.getPrimaryAuthorList():
                keyPA = "%s-%s-%s"%(pAut.getSurName().lower(), pAut.getFirstName().lower(), pAut.getEmail().lower())
                primaryAuthors[keyPA] = pAut
                primaryAuthorEmails.add(pAut.getEmail())
            #Co-authors
            for coAut in abst.getCoAuthorList():
                keyCA = "%s-%s-%s"%(coAut.getSurName().lower(), coAut.getFirstName().lower(), coAut.getEmail().lower())
                coAuthors[keyCA] = coAut
                coAuthorEmails.add(coAut.getEmail())
        emailList = {"submitters":{},"primaryAuthors":{},"coAuthors":{}}
        emailList["submitters"]["tree"] = submitters
        emailList["primaryAuthors"]["tree"] = primaryAuthors
        emailList["coAuthors"]["tree"] = coAuthors
        emailList["submitters"]["emails"] = submitterEmails
        emailList["primaryAuthors"]["emails"] = primaryAuthorEmails
        emailList["coAuthors"]["emails"] = coAuthorEmails
        p = conferences.WPConfParticipantList(self, self._target.getConference(), emailList, self._displayedGroups, self._abstractIds )
        return p.display()


class ContribFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        contribFilters.TypeFilterField.getId():contribFilters.TypeFilterField, \
        contribFilters.StatusFilterField.getId():contribFilters.StatusFilterField, \
        contribFilters.AuthorFilterField.getId():contribFilters.AuthorFilterField, \
        contribFilters.SessionFilterField.getId():contribFilters.SessionFilterField }

class ContribSortingCrit(filters.SortingCriteria):
    _availableFields={\
        contribFilters.NumberSF.getId():contribFilters.NumberSF,
        contribFilters.DateSF.getId():contribFilters.DateSF,
        contribFilters.ContribTypeSF.getId():contribFilters.ContribTypeSF,
        contribFilters.TrackSF.getId():contribFilters.TrackSF,
        contribFilters.SpeakerSF.getId():contribFilters.SpeakerSF,
        contribFilters.BoardNumberSF.getId():contribFilters.BoardNumberSF,
        contribFilters.SessionSF.getId():contribFilters.SessionSF,
        contribFilters.TitleSF.getId():contribFilters.TitleSF
    }


class RHContribList(RHTrackAbstractsBase):

    def _checkProtection(self):
        RHTrackAbstractsBase._checkProtection(self, False)

    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams(self,params)
        self._conf=self._track.getConference()
        filterUsed=params.has_key("OK")
        #sorting
        self._sortingCrit=ContribSortingCrit([params.get("sortBy","number").strip()])
        self._order = params.get("order","down")
        #filtering
        filter = {"author":params.get("authSearch","")}
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append(type.getId())
        else:
            for id in self._normaliseListParam(params.get("types",[])):
                ltypes.append(id)
        filter["type"]=ltypes
        lsessions= []
        if not filterUsed:
            for session in self._conf.getSessionList():
                lsessions.append( session.getId() )
        filter["session"]=self._normaliseListParam(params.get("sessions",lsessions))
        lstatus=[]
        if not filterUsed:
            for status in ContribStatusList().getList():
                lstatus.append(ContribStatusList().getId(status))
        filter["status"]=self._normaliseListParam(params.get("status",lstatus))
        self._filterCrit=ContribFilterCrit(self._conf,filter)
        typeShowNoValue,sessionShowNoValue=True,True
        if filterUsed:
            typeShowNoValue =  params.has_key("typeShowNoValue")
            sessionShowNoValue =  params.has_key("sessionShowNoValue")
        self._filterCrit.getField("type").setShowNoValue(typeShowNoValue)
        self._filterCrit.getField("session").setShowNoValue(sessionShowNoValue)


    
    def _process( self ):
        p = tracks.WPModContribList(self,self._track)
        return p.display( filterCrit= self._filterCrit, sortingCrit=self._sortingCrit, order=self._order )

class RHContribsActions:
    """
    class to select the action to do with the selected contributions
    """
    def __init__(self, req):
        self._req = req
    
    def process(self, params):
        if params.has_key("PDF"):
            return RHContribsToPDF(self._req).process(params)
        elif params.has_key("AUTH"):
            return RHContribsParticipantList(self._req).process(params)
        return "no action to do"

class RHContribsToPDF(RHTrackAbstractsBase):

    def _checkProtection(self):
        RHTrackAbstractsBase._checkProtection(self, False)
    
    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "Contributions.pdf"
        if not self._contribs:
            return "No contributions to print"
        pdf = ConfManagerContribsToPDF(self._conf, self._contribs, tz=tz)
        data = pdf.getPDFBin()
        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.set_content_length(len(data))
        #self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s; name="%s\""""%(mimetype, filename )
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data

class RHContribsParticipantList(RHTrackAbstractsBase):
    
    def _checkProtection( self ):
        if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
            RHTrackAbstractsBase._checkProtection( self )

    def _checkParams( self, params ):
        RHTrackAbstractsBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._displayedGroups = self._normaliseListParam( params.get("displayedGroups", []) )
        self._clickedGroup = params.get("clickedGroup","")

    def _setGroupsToDisplay(self):
        if self._clickedGroup in self._displayedGroups:
            self._displayedGroups.remove(self._clickedGroup)
        else:
            self._displayedGroups.append(self._clickedGroup)
        
    def _process( self ):
        if not self._contribIds:
            return "<table align=\"center\" width=\"100%%\"><tr><td>There are no contributions</td></tr></table>"
        
        speakers = OOBTree()
        primaryAuthors = OOBTree()
        coAuthors = OOBTree()
        speakerEmails = Set()
        primaryAuthorEmails = Set()
        coAuthorEmails = Set()

        self._setGroupsToDisplay()
        for contribId in self._contribIds:
            contrib = self._conf.getContributionById(contribId)
            #Primary authors
            for pAut in contrib.getPrimaryAuthorList():
                if pAut.getFamilyName().lower().strip() == "" and pAut.getFirstName().lower().strip() == "" and pAut.getEmail().lower().strip() == "":
                    continue
                keyPA = "%s-%s-%s"%(pAut.getFamilyName().lower(), pAut.getFirstName().lower(), pAut.getEmail().lower())
                if contrib.isSpeaker(pAut):
                    speakers[keyPA] = pAut
                    speakerEmails.add(pAut.getEmail())
                primaryAuthors[keyPA] = pAut
                primaryAuthorEmails.add(pAut.getEmail())
            #Co-authors
            for coAut in contrib.getCoAuthorList():
                if coAut.getFamilyName().lower().strip() == "" and coAut.getFirstName().lower().strip() == "" and coAut.getEmail().lower().strip() == "":
                    continue
                keyCA = "%s-%s-%s"%(coAut.getFamilyName().lower(), coAut.getFirstName().lower(), coAut.getEmail().lower())
                if contrib.isSpeaker(coAut):
                    speakers[keyCA] = coAut
                    speakerEmails.add(coAut.getEmail())
                coAuthors[keyCA] = coAut
                coAuthorEmails.add(coAut.getEmail())
        emailList = {"speakers":{},"primaryAuthors":{},"coAuthors":{}}
        emailList["speakers"]["tree"] = speakers
        emailList["primaryAuthors"]["tree"] = primaryAuthors
        emailList["coAuthors"]["tree"] = coAuthors
        emailList["speakers"]["emails"] = speakerEmails
        emailList["primaryAuthors"]["emails"] = primaryAuthorEmails
        emailList["coAuthors"]["emails"] = coAuthorEmails
        p = tracks.WPModParticipantList(self, self._target, emailList, self._displayedGroups, self._contribIds )
        return p.display()



class RHContribQuickAccess(RHTrackAbstractsBase):

    def _checkProtection(self):
        RHTrackAbstractsBase._checkProtection(self, False)

    def _checkParams(self,params):
        RHTrackAbstractsBase._checkParams(self,params)
        self._contrib=self._target.getConference().getContributionById(params.get("selContrib",""))

    def _process(self):
        url=urlHandlers.UHTrackModContribList.getURL(self._target)
        if self._contrib is not None:
            url=urlHandlers.UHContributionModification.getURL(self._contrib)
        self._redirect(url)


 
