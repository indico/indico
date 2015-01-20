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


from BTrees.OOBTree import OOBTree
from cStringIO import StringIO

import MaKaC.webinterface.pages.tracks as tracks
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.common.abstractFilters as abstractFilters
import MaKaC.review as review
from MaKaC.webinterface.rh.conferenceBase import RHTrackBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.errors import MaKaCError, FormValuesError
from MaKaC.PDFinterface.conference import TrackManagerAbstractToPDF, TrackManagerAbstractsToPDF
from indico.core.config import Config
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.PDFinterface.conference import ContribsToPDF
from MaKaC.webinterface.mail import GenericMailer, GenericNotification
from MaKaC.i18n import _
from MaKaC.abstractReviewing import ConferenceAbstractReview
from MaKaC.paperReviewing import Answer
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.webinterface.rh.abstractModif import _AbstractWrapper
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
from indico.web.flask.util import send_file


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
            raise MaKaCError( _("You cannot access this option because \"Abstracts\" was disabled"))

    def _process( self ):
        p = tracks.WPTrackModifCoordination( self, self._track )
        return p.display()


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
            raise MaKaCError( _("You cannot access this option because \"Abstracts\" was disabled"))

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
        self._filterUsed = params.has_key( "OK" ) #this variable is true when the
                                            #   filter has been used
        filter = {}
        ltypes = []
        if not self._filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append(type)
        else:
            for id in self._normaliseListParam(params.get("selTypes",[])):
                ltypes.append(self._conf.getContribTypeById(id))
        filter["type"]=ltypes
        lstatus=[]
        if not self._filterUsed:
            sl = tracks.AbstractStatusTrackViewFactory().getStatusList()
            for statusKlass in sl:
                lstatus.append( statusKlass.getId() )
            pass
        filter["status"] = self._normaliseListParam( params.get("selStatus", lstatus) )
        ltypes = []
        if not self._filterUsed:
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
        if self._filterUsed:
            typeShowNoValue =  params.has_key("typeShowNoValue")
            accTypeShowNoValue= params.has_key("accTypeShowNoValue")
        self._criteria.getField("type").setShowNoValue( typeShowNoValue )
        self._criteria.getField("acc_type").setShowNoValue(accTypeShowNoValue)
        self._sortingCrit = TrackAbstractsSortingCrit( self._track, [params.get( "sortBy", "number").strip()] )
        self._selectAll = params.get("selectAll", None)
        self._msg = params.get("directAbstractMsg","")
        self._order = params.get("order","down")


    def _process( self ):
        p = tracks.WPTrackModifAbstracts( self, self._track, self._msg, self._filterUsed, self._order )
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
        if self._abstract == None:
            raise MaKaCError( _("The abstract with id %s does not belong to the track with id %s")%(absId, self._track.getId()))


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


class RHTrackAbstractSetStatusBase(RHTrackAbstractBase):

    """ This is the base class for the accept/reject functionality for the track coordinators  """

    def _checkProtection(self):
        RHTrackAbstractBase._checkProtection(self)
        if  not self._abstract.getConference().getConfAbstractReview().canReviewerAccept():
            raise MaKaCError(_("The acceptance or rejection of abstracts is not allowed. Only the managers of the conference can perform this action."))

    def _checkParams(self, params):
        RHTrackAbstractBase._checkParams(self, params)
        self._action = params.get("accept", None)
        if self._action:
            self._typeId = params.get("type", "")
            self._session=self._conf.getSessionById(params.get("session", ""))
        else:
            self._action = params.get("reject", None)
        self._comments = params.get("comments", "")
        self._doNotify = params.has_key("notify")

    def _notifyStatus(self, status):
        wrapper = _AbstractWrapper(status)
        tpl = self._abstract.getOwner().getNotifTplForAbstract(wrapper)
        if self._doNotify and tpl:
            n = EmailNotificator()
            self._abstract.notify(n, self._getUser())


class RHTrackAbstractAccept(RHTrackAbstractSetStatusBase):

    def _process(self):
        if self._action:
            cType = self._abstract.getConference().getContribTypeById(self._typeId)
            self._abstract.accept(self._getUser(), self._track, cType, self._comments, self._session)
            self._notifyStatus(review.AbstractStatusAccepted(self._abstract, None, self._track, cType))
            self._redirect(urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract ))
        else:
            p = tracks.WPTrackAbstractAccept(self, self._track, self._abstract)
            return p.display(**self._getRequestParams())


class RHTrackAbstractReject(RHTrackAbstractSetStatusBase):

    def _process(self):
        if self._action:
            self._abstract.reject(self._getUser(), self._comments)
            self._notifyStatus(review.AbstractStatusRejected(self._abstract, None, None))
            self._redirect(urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract ))
        else:
            p = tracks.WPTrackAbstractReject(self, self._track, self._abstract)
            return p.display(**self._getRequestParams())


class RHTrackAbstractPropBase(RHTrackAbstractBase):
    """ Base class for propose to accept/reject classes """

    def _checkParams(self,params):
        RHTrackAbstractBase._checkParams(self,params)
        self._action = ""
        self._comment = params.get("comment","")
        self._answers = []
        if params.has_key("OK"):
            self._action = "GO"
            # get answers and make the list
            scaleLower = self._target.getConference().getConfAbstractReview().getScaleLower()
            scaleHigher = self._target.getConference().getConfAbstractReview().getScaleHigher()
            numberOfAnswers = self._target.getConference().getConfAbstractReview().getNumberOfAnswers()
            c = 0
            for question in self._target.getConference().getConfAbstractReview().getReviewingQuestions():
                c += 1
                if not params.has_key("RB_"+str(c)):
                    raise FormValuesError(_("Please, reply to all the reviewing questions. Question \"%s\" is missing the answer.")%question.getText())
                rbValue = int(params.get("RB_"+str(c),scaleLower))
                newId = self._target.getConference().getConfAbstractReview().getNewAnswerId()
                newAnswer = Answer(newId, rbValue, numberOfAnswers, question)
                newAnswer.calculateRatingValue(scaleLower, scaleHigher)
                self._answers.append(newAnswer)
        elif params.has_key("CANCEL"):
            self._action="CANCEL"


class RHTrackAbstractPropToAccept( RHTrackAbstractPropBase ):

    def _checkParams(self,params):
        RHTrackAbstractPropBase._checkParams(self,params)
        self._contribType = params.get("contribType",self._abstract.getContribType())
        if params.has_key("OK"):
            ctId = ""
            if self._abstract.getContribType():
                ctId = self._abstract.getContribType().getId()
            ctId = params.get("contribType",ctId)
            self._contribType = self._abstract.getConference().getContribTypeById(ctId)

    def _process( self ):
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract )
        if self._action == "CANCEL":
            self._redirect( url )
        elif self._action == "GO":
            r = self._getUser()
            self._abstract.proposeToAccept( r, self._track, self._contribType, self._comment, self._answers )
            self._redirect( url )
        else:
            p=tracks.WPTrackAbstractPropToAcc(self,self._track,self._abstract)
            return p.display(contribType=self._contribType,\
                                comment=self._comment)


class RHTrackAbstractPropToReject( RHTrackAbstractPropBase ):

    def _process( self ):
        url = urlHandlers.UHTrackAbstractModif.getURL( self._track, self._abstract )
        if self._action == "CANCEL":
            self._redirect( url )
        elif self._action == "GO":
            r = self._getUser()
            self._abstract.proposeToReject( r, self._track, self._comment , self._answers)
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

    def _checkParams(self, params):
        RHTrackAbstractBase._checkParams(self, params)
        self._action, self._comments, self._original = "", "", None
        self._originalId = ""
        if "OK" in params:
            self._action = "MARK"
            self._comments = params.get("comments", "")
            self._originalId = params.get("id", "")
            self._original = self._abstract.getOwner(
            ).getAbstractById(self._originalId)

    def _process(self):
        if self._action == "MARK":
            if self._original is None or self._target == self._original:
                raise MaKaCError(_("invalid original abstract id"))
            self._abstract.markAsDuplicated(
                self._getUser(), self._original, self._comments, self._track)
            self._redirect(urlHandlers.UHTrackAbstractModif.getURL(
                self._track, self._abstract))
            return
        p = tracks.WPModAbstractMarkAsDup(self, self._track, self._abstract)
        return p.display(comments=self._comments, originalId=self._originalId)


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

    def _process(self):
        tz = self._conf.getTimezone()
        filename = "%s - Abstract.pdf" % self._target.getTitle()
        pdf = TrackManagerAbstractToPDF(self._abstract, self._track, tz=tz)
        return send_file(filename, pdf.generate(), 'PDF')


class RHAbstractsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        assert req is None

    def _checkParams( self, params ):
        self._pdf = params.get("PDF.x", None)
        self._mail = params.get("mail", None)
        self._participant = params.get("PART", None)
        self._tplPreview = params.get("tplPreview", None)
        self._params = params


    def _process( self ):
        if self._pdf:
            return RHAbstractsToPDF(None).process( self._params )
        elif self._mail:
            return RHAbstractSendNotificationMail(None).process( self._params )
        elif self._tplPreview:
            return RHAbstractTPLPreview(None).process( self._params )
        elif self._participant:
            return RHAbstractsParticipantList(None).process( self._params )
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


    def _process(self):
        tz = self._conf.getTimezone()
        if not self._abstractIds:
            return "No abstract to print"
        pdf = TrackManagerAbstractsToPDF(self._conf, self._track, self._abstractIds,tz=tz)
        return send_file('Abstracts.pdf', pdf.generate(), 'PDF')


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
        submitterEmails = set()
        primaryAuthorEmails = set()
        coAuthorEmails = set()

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
        assert req is None

    def process(self, params):
        if 'PDF' in params:
            return RHContribsToPDF(None).process(params)
        elif 'AUTH' in params:
            return RHContribsParticipantList(None).process(params)
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

    def _process(self):
        tz = self._conf.getTimezone()
        if not self._contribs:
            return "No contributions to print"
        pdf = ContribsToPDF(self._conf, self._contribs)
        return send_file('Contributions.pdf', pdf.generate(), 'PDF')


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
        speakerEmails = set()
        primaryAuthorEmails = set()
        coAuthorEmails = set()

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



