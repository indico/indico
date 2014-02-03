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
from cStringIO import StringIO
from flask import request

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.abstracts as abstracts
import MaKaC.review as review
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHAbstractBase, RHConferenceBase
from MaKaC.PDFinterface.conference import ConfManagerAbstractToPDF
from MaKaC.common.xmlGen import XMLGen
from MaKaC.errors import MaKaCError, ModificationError, FormValuesError, NoReportError
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
from indico.core.config import Config
from MaKaC.webinterface.common.abstractDataWrapper import AbstractParam
from MaKaC.i18n import _
from MaKaC.webinterface.rh.conferenceModif import CFAEnabled
from MaKaC.paperReviewing import Answer
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from indico.web.flask.util import send_file
from MaKaC.PDFinterface.base import LatexRunner


class RHAbstractModifBase( RHAbstractBase, RHModificationBaseProtected ):
    """ Base class to be used for abstract modification in the admin interface,
        when the request can only be performed by Conference managers.
    """

    def _checkParams( self, params ):
        RHAbstractBase._checkParams( self, params )

    def _checkProtection( self ):
        target = self._target
        try:
            self._target = self._conf
            RHModificationBaseProtected._checkProtection(self)
        finally:
            self._target = target
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


class RHAbstractManagment(RHAbstractModifBase):

    def _process( self ):
        p = abstracts.WPAbstractManagment( self, self._target )
        return p.display( **self._getRequestParams() )


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
        filename = "%s - Abstract.pdf" % self._target.getTitle()
        pdf = ConfManagerAbstractToPDF(self._target, tz=tz)
        return send_file(filename, pdf.generate(), 'PDF')


class RHAbstractToXML(RHAbstractModifBase):

    def _process( self ):
        filename = "%s - Abstract.xml"%self._target.getTitle()

        x = XMLGen()
        x.openTag("abstract")
        x.writeTag("Id", self._target.getId())
        x.writeTag("Title", self._target.getTitle())
        afm = self._target.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getFields():
            id = f.getId()
            if f.isActive() and str(self._target.getField(id)).strip() != "":
                x.writeTag("field",self._target.getField(id),[("id",id)])
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

        return send_file(filename, StringIO(x.getXml()), 'XML')


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
        self._doNotify=params.has_key("notify")

    def _process( self ):
        if self._accept:
            cType=self._conf.getContribTypeById(self._typeId)
            st=review.AbstractStatusAccepted(self._target,None,self._track,cType)
            wrapper=_AbstractWrapper(st)
            tpl=self._target.getOwner().getNotifTplForAbstract(wrapper)
            if self._doNotify and not self._warningShown and tpl is None:
                p=abstracts.WPModAcceptConfirmation(self,self._target)
                return p.display(track=self._trackId,comments=self._comments,type=self._typeId,session=self._sessionId)
            else:
                self._target.accept(self._getUser(),self._track,cType,self._comments,self._session)
                if self._doNotify:
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
        self._doNotify=params.has_key("notify")
        self._warningShown=params.has_key("confirm")

    def _process( self ):
        if self._reject:
            st=review.AbstractStatusRejected(self._target,None,None)
            wrapper=_AbstractWrapper(st)
            tpl=self._target.getOwner().getNotifTplForAbstract(wrapper)
            if self._doNotify and not self._warningShown and tpl is None:
                p=abstracts.WPModRejectConfirmation(self,self._target)
                return p.display(comments=self._comments)
            else:
                self._target.reject(self._getUser(), self._comments)
                if self._doNotify:
                    n=EmailNotificator()
                    self._target.notify(n,self._getUser())
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
        else:
            p = abstracts.WPAbstractManagmentReject( self, self._target )
            return p.display( **self._getRequestParams() )


class RHMarkAsDup(RHAbstractModifBase):

    def _checkParams(self, params):
        RHAbstractModifBase._checkParams(self, params)
        self._action, self._comments, self._original = "", "", None
        self._originalId = ""
        if "OK" in params:
            self._action = "MARK"
            self._comments = params.get("comments", "")
            self._originalId = params.get("id", "")
            self._original = self._target.getOwner().getAbstractById(self._originalId)

    def _getErrorsInData(self):
        res = []
        if self._original is None or self._target == self._original:
            res.append(_("invalid original abstract id"))
        return res

    def _process(self):
        errMsg = ""
        if self._action == "MARK":
            errorList = self._getErrorsInData()
            if len(errorList) == 0:
                self._target.markAsDuplicated(
                    self._getUser(), self._original, self._comments)
                self._redirect(
                    urlHandlers.UHAbstractManagment.getURL(self._target))
                return
            else:
                errMsg = "<br>".join(errorList)
        p = abstracts.WPModMarkAsDup(self, self._target)
        return p.display(comments=self._comments, originalId=self._originalId, errorMsg=errMsg)


class RHUnMarkAsDup(RHAbstractModifBase):

    def _checkParams(self, params):
        RHAbstractModifBase._checkParams(self, params)
        self._action, self._comments, self._original = "", "", None
        self._originalId = ""
        if "OK" in params:
            self._action = "UNMARK"
            self._comments = params.get("comments", "")

    def _process(self):
        errMsg = ""
        if self._action == "UNMARK":
            self._target.unMarkAsDuplicated(self._getUser(), self._comments)
            self._redirect(
                urlHandlers.UHAbstractManagment.getURL(self._target))
            return
        p = abstracts.WPModUnMarkAsDup(self, self._target)
        return p.display(comments=self._comments, originalId=self._originalId, errorMsg=errMsg)


class RHMergeInto(RHAbstractModifBase):

    def _checkParams(self, params):
        RHAbstractModifBase._checkParams(self, params)
        self._action, self._comments, self._targetAbs = "", "", None
        self._targetAbsId, self._includeAuthors, self._doNotify = "", False, True
        if "OK" in params:
            self._action = "MERGE"
            self._comments = params.get("comments", "")
            self._targetAbsId = params.get("id", "")
            self._includeAuthors = "includeAuthors" in params
            self._doNotify = "notify" in params
            self._targetAbs = self._target.getOwner(
            ).getAbstractById(self._targetAbsId)

    def _getErrorsInData(self):
        res = []
        if self._targetAbs is None or self._target == self._targetAbs:
            res.append("invalid target abstract id")
        return res

    def _process(self):
        errMsg = ""
        if self._action == "MERGE":
            errorList = self._getErrorsInData()
            if len(errorList) == 0:
                self._target.mergeInto(self._getUser(), self._targetAbs, comments=self._comments, mergeAuthors=self._includeAuthors)
                if self._doNotify:
                    self._target.notify(EmailNotificator(), self._getUser())
                self._redirect(
                    urlHandlers.UHAbstractManagment.getURL(self._target))
                return
            else:
                errMsg = "<br>".join(errorList)
        p = abstracts.WPModMergeInto(self, self._target)
        return p.display(comments=self._comments, targetId=self._targetAbsId, errorMsg=errMsg, includeAuthors=self._includeAuthors, notify=self._doNotify)

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


class RHPropBase(RHAbstractModifBase):

    def _checkProtection(self):
        try:
            RHAbstractModifBase._checkProtection(self)
        except ModificationError,e:
            if self._target.isAllowedToCoordinate(self._getUser()):
                return
            raise

    def _checkParams( self, params ):
        RHAbstractModifBase._checkParams(self, params)
        self._action = ""
        self._answers = []
        if params.has_key("OK"):
            self._action = "GO"
            conf=self._target.getConference()
            self._track = conf.getTrackById(params.get("track",""))
            if self._track is None:
                raise FormValuesError( _("You have to choose a track in order to do the proposal. If there are not tracks to select, please change the track assignment of the abstract from its management page"))
            self._contribType = self._conf.getContribTypeById(params.get("contribType",""))
            self._comment = params.get("comment","")
            scaleLower = conf.getConfAbstractReview().getScaleLower()
            scaleHigher = conf.getConfAbstractReview().getScaleHigher()
            numberOfAnswers = conf.getConfAbstractReview().getNumberOfAnswers()
            c = 0
            for question in conf.getConfAbstractReview().getReviewingQuestions():
                c += 1
                if not params.has_key("RB_"+str(c)):
                    raise FormValuesError(_("Please, reply to all the reviewing questions. Question \"%s\" is missing the answer.")%question.getText())
                rbValue = int(params.get("RB_"+str(c),scaleLower))
                newId = conf.getConfAbstractReview().getNewAnswerId()
                newAnswer = Answer(newId, rbValue, numberOfAnswers, question)
                newAnswer.calculateRatingValue(scaleLower, scaleHigher)
                self._answers.append(newAnswer)
        elif params.has_key("CANCEL"):
            self._action="CANCEL"


class RHPropToAcc(RHPropBase):

    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if self._action=="GO":
            self._abstract.proposeToAccept(self._getUser(),\
                self._track,self._contribType,self._comment, self._answers)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=abstracts.WPModPropToAcc(self,self._target)
            return p.display()



class RHPropToRej(RHPropBase):

    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if self._action=="GO":
            self._abstract.proposeToReject(self._getUser(),\
                self._track,self._comment, self._answers)
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

    def _removeAssociatedContribution(self):
        contribution = self._abstract.getContribution()
        contribution.getOwner().getSchedule().removeEntry(contribution.getSchEntry())
        contribution.delete()

    def _process( self ):
        url=urlHandlers.UHAbstractManagment.getURL(self._target)
        if isinstance(self._abstract.getCurrentStatus(), (review.AbstractStatusWithdrawn, review.AbstractStatusRejected)):
            self._abstract.setCurrentStatus(review.AbstractStatusSubmitted(self._abstract))
        elif isinstance(self._abstract.getCurrentStatus(), review.AbstractStatusAccepted):
            # remove the associated contribution
            self._removeAssociatedContribution()
            # set submittted status
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

    def _process( self ):
        p = abstracts.WPAbstractTrackManagment( self, self._target )
        return p.display( **self._getRequestParams() )

class RHAbstractTrackOrderByRating(RHAbstractModifBase):

    def _process( self ):
        p = abstracts.WPAbstractTrackOrderByRating( self, self._target )
        return p.display( **self._getRequestParams() )


class RHEditData(RHAbstractModifBase, AbstractParam):

    def __init__(self, req):
        RHAbstractModifBase.__init__(self, req)
        AbstractParam.__init__(self)

    def _checkParams(self, params):
        RHAbstractModifBase._checkParams(self,params)
        if self._getUser() is None:
            return
        AbstractParam._checkParams(self, params, self._conf, request.content_length)
        if self._action == "":#First call
            #TODO: remove this code, this should be handle by AbstractData (not method available
            # because setAbstractData(abstract) is used when saving, so there are specific actions.
            afm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
            self._abstractData.title = self._abstract.getTitle()
            for f in afm.getFields():
                id = f.getId()
                self._abstractData.setFieldValue(id, self._abstract.getField(id))
            self._abstractData.type = self._abstract.getContribType()
            trackIds = []
            for track in self._abstract.getTrackListSorted():
                trackIds.append(track.getId())
            self._abstractData.tracks = trackIds
            self._abstractData.comments = self._abstract.getComments()

    def _doValidate( self ):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = abstracts.WPModEditData(self, self._target, self._abstractData)
            pars = self._abstractData.toDict()
            pars["errors"] = errors
            pars["action"] = self._action
            # restart the current value of the param attachments to show the existing files
            pars["attachments"] = self._abstract.getAttachments().values()
            return p.display( **pars )
        self._abstract.clearAuthors()
        #self._setAbstractData(self._abstract)
        self._abstractData.setAbstractData(self._abstract)
        self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))

    def _process( self ):
        if self._action == "CANCEL":
            self._redirect(urlHandlers.UHAbstractManagment.getURL(self._target))
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            if isinstance( self._abstract.getCurrentStatus(), review.AbstractStatusAccepted ):
                raise NoReportError(_("The abstract with id '%s' cannot be edited because it has already been accepted.") % self._abstract.getId())
            p = abstracts.WPModEditData(self, self._target, self._abstractData)
            pars = self._abstractData.toDict()
            return p.display(**pars)


class RHIntComments(RHAbstractModifBase):

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

    def _process( self ):
        p = abstracts.WPModNotifLog(self,self._target)
        return p.display()

class RHTools(RHAbstractModifBase):

    def _process( self ):
        p = abstracts.WPModTools(self,self._target)
        return p.display()





