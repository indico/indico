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
from flask import request

from textwrap import TextWrapper

from BTrees.IOBTree import IOBTree
from cStringIO import StringIO

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.mail as mail
import MaKaC.webinterface.pages.abstracts as abstracts
import MaKaC.review as review
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from indico.core.db import DBMgr
from MaKaC.review import AbstractStatusSubmitted, AbstractStatusAccepted
from MaKaC.PDFinterface.conference import AbstractToPDF, AbstractsToPDF
from MaKaC.errors import MaKaCError, NoReportError
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.web.flask.util import send_file
from MaKaC.webinterface.common.abstractDataWrapper import AbstractParam
from MaKaC.webinterface.rh.fileAccess import RHFileAccess
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.PDFinterface.base import LatexRunner


class RHBaseCFA( RHConferenceBaseDisplay ):

    def _processIfActive( self ):
        """only override this method if the CFA must be activated for
            carrying on the handler execution"""
        return "cfa"

    def _process( self ):
        #if the CFA is not activated we show up a form informing about that.
        #   This must be done at RH level because there can be some RH not
        #   displaying pages.
        cfaMgr = self._conf.getAbstractMgr()
        if not cfaMgr.isActive() or not self._conf.hasEnabledSection("cfa"):
            p = abstracts.WPCFAInactive( self, self._conf )
            return p.display()
        else:
            return self._processIfActive()


class RHConferenceCFA( RHBaseCFA ):
    _uh = urlHandlers.UHConferenceCFA

    def _processIfActive( self ):
        p = abstracts.WPConferenceCFA( self, self._target )
        return p.display()


class RHAbstractSubmissionBase(RHBaseCFA):

    def _checkProtection(self):
        self._checkSessionUser()
        RHBaseCFA._checkProtection(self)

    def _processIfOpened(self):
        """only override this method if the submission period must be opened
            for the request handling"""
        return "cfa opened"

    def _processIfActive(self):
        cfaMgr = self._conf.getAbstractMgr()
        #if the user is in the autorized list, don't check period
        if self._getUser() in cfaMgr.getAuthorizedSubmitterList():
            return self._processIfOpened()
        #if the submission period is not yet opened we show up a form informing
        #   about that.
        if timezoneUtils.nowutc() < cfaMgr.getStartSubmissionDate():
        #if the submission period is already closed we show up a form informing
        #   about that.
            p = abstracts.WPCFANotYetOpened(self, self._conf)
            return p.display()
        elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate():
            p = abstracts.WPCFAClosed(self, self._conf, False)
            return p.display()
        else:
            return self._processIfOpened()


class _AbstractSubmissionNotification:

    def __init__(self, abstract):
        self._abstract = abstract
        self._conf = self._abstract.getConference()
        self._subject = _("Abstract submission confirmation (%s)") % self._conf.getTitle()

    def getAttachments(self):
        return []

    def getSubject(self):
        return self._subject

    def setSubject(self, s):
        self._subject = s

    def getDestination(self):
        return self._abstract.getSubmitter()

    def getFromAddr(self):
        return self._conf.getSupportInfo().getEmail(returnNoReply=True)

    def getCCList(self):
        return self._abstract.getOwner().getSubmissionNotification().getCCList()

    def getToList(self):
        return self._abstract.getOwner().getSubmissionNotification().getToList()

    def getMsg(self):
        primary_authors = []
        for auth in self._abstract.getPrimaryAuthorList():
            primary_authors.append("""%s (%s) <%s>""" % (auth.getFullName(), auth.getAffiliation(), auth.getEmail()))
        co_authors = []
        for auth in self._abstract.getCoAuthorList():
            email = ""
            if auth.getEmail() != "":
                email = " <%s>" % auth.getEmail()
            co_authors.append("""%s (%s)%s""" % (auth.getFullName(), auth.getAffiliation(), email))
        speakers = []
        for spk in self._abstract.getSpeakerList():
            speakers.append(spk.getFullName())
        tracks = []
        for track in self._abstract.getTrackListSorted():
            tracks.append("""%s""" % track.getTitle())
        tw = TextWrapper()
        msg = [i18nformat("""_("Dear") %s,""") % self._abstract.getSubmitter().getStraightFullName()]
        msg.append("")
        msg.append(tw.fill(_("The submission of your abstract has been successfully processed.")))
        msg.append("")
        tw.break_long_words = False
        msg.append(tw.fill(i18nformat("""_("Abstract submitted"):\n<%s>.""") % urlHandlers.UHUserAbstracts.getURL(self._conf)))
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Status of your abstract"):\n<%s>.""") % urlHandlers.UHAbstractDisplay.getURL(self._abstract)))
        msg.append("")
        tw.subsequent_indent = ""
        msg.append(tw.fill(i18nformat("""_("See below a detailed summary of your submitted abstract"):""")))
        msg.append("")
        tw.subsequent_indent = " "*3
        msg.append(tw.fill(i18nformat("""_("Conference"): %s""") % self._conf.getTitle()))
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Submitted by"): %s""") % self._abstract.getSubmitter().getFullName()))
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Submitted on"): %s""") % self._abstract.getSubmissionDate().strftime("%d %B %Y %H:%M")))
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Title"): %s""") % self._abstract.getTitle()))
        msg.append("")
        for f in self._conf.getAbstractMgr().getAbstractFieldsMgr().getFields():
            msg.append(tw.fill(f.getCaption()))
            msg.append(str(self._abstract.getField(f.getId())))
            msg.append("")
        msg.append(tw.fill(i18nformat("""_("Primary Authors"):""")))
        msg += primary_authors
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Co-authors"):""")))
        msg += co_authors
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Abstract presenters"):""")))
        msg += speakers
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Track classification"):""")))
        msg += tracks
        msg.append("")
        ctype = i18nformat("""--_("not specified")--""")
        if self._abstract.getContribType() is not None:
            ctype = self._abstract.getContribType().getName()
        msg.append(tw.fill(i18nformat("""_("Presentation type"): %s""") % ctype))
        msg.append("")
        msg.append(tw.fill(i18nformat("""_("Comments"): %s""") % self._abstract.getComments()))
        msg.append("")
        return "\n".join(msg)

    def getBody(self):
        msg = self.getMsg()
        return i18nformat("""
_("The following email has been sent to %s"):

===

%s""") % (self.getDestination().getFullName(), msg)


class RHAbstractModificationAction(RHAbstractSubmissionBase, AbstractParam):

    def __init__(self, req):
        RHAbstractSubmissionBase.__init__(self, req)
        AbstractParam.__init__(self)

    def _checkParams( self, params ):
        RHAbstractSubmissionBase._checkParams(self, params)
        #if the user is not logged in we return immediately as this form needs
        #   the user to be logged in and therefore all the checking below is not
        #   necessary
        if self._getUser() is None:
            return

        AbstractParam._checkParams(self, params, self._conf, request.content_length)


class RHAbstractSubmission( RHAbstractModificationAction ):
    _uh = urlHandlers.UHAbstractSubmission

    def _doValidate( self ):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = abstracts.WPAbstractSubmission( self, self._target )
            pars = self._abstractData.toDict()
            pars["action"] = self._action
            pars["attachments"] = []
            return p.display( **pars )
        #Then, we create the abstract object and set its data to the one
        #   received
        cfaMgr = self._target.getAbstractMgr()
        abstract = cfaMgr.newAbstract( self._getUser() )
        self._abstractData.setAbstractData(abstract)
        #The commit must be forced before sending the confirmation
        DBMgr.getInstance().commit()
        #Email confirmation about the submission
        mail.Mailer.send( _AbstractSubmissionNotification( abstract ), self._conf.getSupportInfo().getEmail(returnNoReply=True) )
        #Email confirmation about the submission to coordinators
        if cfaMgr.getSubmissionNotification().hasDestination():
            asn=_AbstractSubmissionNotification( abstract )
            asn.setSubject(_("[Indico] New abstract submission: %s")%asn.getDestination().getFullName())
            mail.GenericMailer.send( asn )
        #We must perform some actions: email warning to the authors
        #Finally, we display a confirmation form
        self._redirect( urlHandlers.UHAbstractSubmissionConfirmation.getURL( abstract ) )

    def _processIfOpened( self ):
        if self._action == "CANCEL":
            self._redirect( urlHandlers.UHConferenceCFA.getURL( self._conf ) )
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            p = abstracts.WPAbstractSubmission( self, self._target )
            pars = self._abstractData.toDict()
            return p.display( **pars )


class RHAbstractModify(RHAbstractModificationAction, RHModificationBaseProtected):
    _uh = urlHandlers.UHAbstractModify

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    def _checkParams(self, params):
        RHAbstractModificationAction._checkParams(self, params)
        if self._getUser() is None:
            return
        if self._action == "":
            #First call
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

    def _processIfActive(self):
        #We overload this method to allow modification after the CFA is closed if the modification deadline is after the submission deadline
        cfaMgr = self._conf.getAbstractMgr()
        modifDeadLine = cfaMgr.getModificationDeadline()
        if not modifDeadLine:
            modifDeadLine = cfaMgr.getEndSubmissionDate()
        #if the user is in the autorized list, don't check period
        if self._getUser() in cfaMgr.getAuthorizedSubmitterList():
            return self._processIfOpened()
        #if the submission period is not yet opened we show up a form informing
        #   about that.
        if timezoneUtils.nowutc() < cfaMgr.getStartSubmissionDate():
        #if the submission period is already closed we show up a form informing
        #   about that.
            p = abstracts.WPCFANotYetOpened(self, self._conf)
            return p.display()
        #elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() :
        elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() and timezoneUtils.nowutc() > modifDeadLine:
            p = abstracts.WPCFAClosed(self, self._conf, True)
            return p.display()
        else:
            return self._processIfOpened()

    def _doValidate(self):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = abstracts.WPAbstractModify(self, self._target)
            pars = self._abstractData.toDict()
            pars["action"] = self._action
            # restart the current value of the param attachments to show the existing files
            pars["attachments"] = self._abstract.getAttachments().values()
            return p.display(**pars)
        self._abstract.clearAuthors()
        self._abstractData.setAbstractData(self._abstract)
        self._redirect(urlHandlers.UHAbstractDisplay.getURL(self._abstract))

    def _processIfOpened(self):
        #check if the modification period is not over or if the abstract
        #   is in a different status than Submitted
        if not self._conf.getAbstractMgr().inModificationPeriod() or \
                not isinstance(self._abstract.getCurrentStatus(),
                               AbstractStatusSubmitted):
            wp = abstracts.WPAbstractCannotBeModified(self, self._abstract)
            return wp.display()
        if self._action == "CANCEL":
            self._redirect(urlHandlers.UHAbstractDisplay.getURL(self._abstract))
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            p = abstracts.WPAbstractModify(self, self._target)
            pars = self._abstractData.toDict()
            pars["action"] = self._action
            return p.display(**pars)


class RHUserAbstracts( RHAbstractSubmissionBase ):
    _uh = urlHandlers.UHUserAbstracts

    def _processIfActive( self ):
        p = abstracts.WPUserAbstracts( self, self._conf )
        return p.display()


class RHAbstractDisplayBase( RHAbstractSubmissionBase ):

    def _checkParams( self, params ):
        RHAbstractSubmissionBase._checkParams( self, params )
        cfaMgr = self._conf.getAbstractMgr()
        if not params.has_key("abstractId") and params.has_key("contribId"):
            params["abstractId"] = params["contribId"]
        self._abstract = self._target = cfaMgr.getAbstractById( params["abstractId"] )
        if self._abstract == None:
            raise NoReportError(_("The abstract you are trying to access does not exist or has been deleted"))


class RHAbstractSubmissionConfirmation( RHAbstractDisplayBase ):
    _uh = urlHandlers.UHAbstractSubmissionConfirmation

    def _processIfOpened( self ):
        p = abstracts.WPAbstractSubmissionConfirmation( self, self._target )
        return p.display()


class RHAbstractDisplay( RHAbstractDisplayBase ):
    _uh = urlHandlers.UHAbstractDisplay

    def _processIfActive( self ):
        p = abstracts.WPAbstractDisplay( self, self._target )
        return p.display()


class RHAbstractDisplayPDF( RHAbstractDisplayBase ):

    def _checkProtection( self ):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("The Call For Abstracts was disabled by the conference managers"))

    def _process(self):
        tz = timezoneUtils.DisplayTZ(self._aw, self._conf).getDisplayTZ()
        filename = '%s - Abstract.pdf' % self._target.getTitle()
        pdf = AbstractToPDF(self._target, tz=tz)
        return send_file(filename, pdf.generate(), 'PDF')


class RHUserAbstractsPDF(RHAbstractSubmissionBase):

    def _processIfActive(self):
        tz = timezoneUtils.DisplayTZ(self._aw, self._conf).getDisplayTZ()
        cfaMgr = self._conf.getAbstractMgr()
        abstracts = set(cfaMgr.getAbstractListForAvatar(self._aw.getUser()))
        abstracts |= set(cfaMgr.getAbstractListForAuthorEmail(self._aw.getUser().getEmail()))
        self._abstractIds = sorted(abstract.getId() for abstract in abstracts)
        if not self._abstractIds:
            return _("No abstract to print")

        filename = 'my-abstracts.pdf'
        pdf = AbstractsToPDF(self._conf, self._abstractIds, tz=tz)
        return send_file(filename, pdf.generate(), 'PDF')


class RHAbstractModificationBase(RHAbstractDisplayBase, RHModificationBaseProtected):

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    def _processIfActive(self):
        #We overload this method to alow modification after the CFA is closed if the modification deadline is after the submission deadline
        cfaMgr = self._conf.getAbstractMgr()
        modifDeadLine = cfaMgr.getModificationDeadline()
        if not modifDeadLine:
            modifDeadLine = cfaMgr.getEndSubmissionDate()
        #if the user is in the autorized list, don't check period
        if self._getUser() in cfaMgr.getAuthorizedSubmitterList():
            return self._processIfOpened()
        #if the submission period is not yet opened we show up a form informing
        #   about that.
        if timezoneUtils.nowutc() < cfaMgr.getStartSubmissionDate():
        #if the submission period is already closed we show up a form informing
        #   about that.
            p = abstracts.WPCFANotYetOpened(self, self._conf)
            return p.display()
        #elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() :
        elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() and timezoneUtils.nowutc() > modifDeadLine:
            p = abstracts.WPCFAClosed(self, self._conf, True)
            return p.display()
        else:
            return self._processIfOpened()


class RHAbstractWithdraw( RHAbstractModificationBase ):
    _uh = urlHandlers.UHAbstractWithdraw

    def _checkParams( self, params ):
        RHAbstractModificationBase._checkParams( self, params )
        self._action = ""
        self._comments = params.get( "comment", "" )
        if params.has_key("OK"):
            self._action = "WITHDRAW"
        elif params.has_key("cancel"):
            self._action = "CANCEL"

    def _processIfOpened( self ):
        if self._action == "CANCEL":
            self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )
        elif self._action == "WITHDRAW":
            if self._abstract.getCurrentStatus().__class__ not in \
                    [review.AbstractStatusSubmitted,
                    review.AbstractStatusUnderReview,
                    review.AbstractStatusInConflict,
                    review.AbstractStatusProposedToAccept,
                    review.AbstractStatusProposedToReject]:
                raise MaKaCError( _("this abstract cannot be withdrawn, please contact the conference organisers in order to do so"))
            self._abstract.withdraw(self._getUser(),self._comments)
            self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )
        else:
            wp = abstracts.WPAbstractWithdraw( self, self._abstract )
            return wp.display()


class RHAbstractRecovery( RHAbstractModificationBase ):
    _uh = urlHandlers.UHAbstractWithdraw

    def _checkParams( self, params ):
        RHAbstractModificationBase._checkParams( self, params )
        self._action = ""
        if params.has_key("OK"):
            self._action = "RECOVER"
        elif params.has_key("cancel"):
            self._action = "CANCEL"

    def _processIfOpened( self ):
        if self._action == "CANCEL":
            self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )
        elif self._action == "RECOVER":
            status=self._abstract.getCurrentStatus()
            if isinstance(status,review.AbstractStatusWithdrawn):
                if status.getResponsible()!=self._getUser():
                    raise MaKaCError( _("you are not allowed to recover this abstract"))
                self._abstract.recover()
            self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )
        else:
            wp = abstracts.WPAbstractRecovery( self, self._abstract )
            return wp.display()

class RHGetAttachedFile(RHFileAccess):

    def _checkProtection( self ):
        if not self._conf.getAbstractMgr().showAttachedFilesContribList():
            # Same protection as the abstract
            temptarget=self._target
            self._target = self._target.getOwner()
            RHFileAccess._checkProtection( self )
            self._target = temptarget
