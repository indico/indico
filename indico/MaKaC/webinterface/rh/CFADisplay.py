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

import os
from textwrap import TextWrapper

from BTrees.IOBTree import IOBTree
from datetime import datetime

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.mail as mail
import MaKaC.webinterface.pages.abstracts as abstracts
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.review as review
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.common import DBMgr,Config
from MaKaC.review import AbstractStatusSubmitted
from MaKaC.PDFinterface.conference import AbstractToPDF, AbstractsToPDF
from MaKaC.webinterface.general import normaliseListParam
from MaKaC.errors import MaKaCError
import MaKaC.common.timezoneUtils as timezoneUtils
import MaKaC.conference as conference
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _


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


class RHAbstractSubmissionBase( RHBaseCFA ):

    def _checkProtection( self ):
        self._checkSessionUser()
        RHBaseCFA._checkProtection( self )

    def _processIfOpened( self ):
        """only override this method if the submission period must be opened
            for the request handling"""
        return "cfa opened"

    def _processIfActive( self ):
        cfaMgr = self._conf.getAbstractMgr()
        #if the user is in the autorized list, don't check period
        if self._getUser() in cfaMgr.getAuthorizedSubmitterList():
            return self._processIfOpened()
        #if the submission period is not yet opened we show up a form informing
        #   about that.
        if timezoneUtils.nowutc() < cfaMgr.getStartSubmissionDate():
        #if the submission period is already closed we show up a form informing
        #   about that.
            p = abstracts.WPCFANotYetOpened( self, self._conf )
            return p.display()
        elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() :
            p = abstracts.WPCFAClosed( self, self._conf )
            return p.display()
        else:
            return self._processIfOpened()


class _AbstractAuthorList:

    def __init__( self, params ):
        self._mapFromParams( params )

    def _getAuthorFromParams( self, idx, params ):
        author = {  "auth_id": int( params["auth_id"][idx].strip() ), \
                "auth_title": params["auth_title"][idx].strip(), \
                "auth_firstName": params["auth_firstName"][idx].strip(), \
                "auth_surName": params["auth_surName"][idx].strip(), \
                "auth_affiliation": params["auth_affiliation"][idx].strip(), \
                "auth_email": params["auth_email"][idx].strip(), \
                "auth_phone": params["auth_phone"][idx].strip(), \
                "auth_address": params["auth_address"][idx].strip(), \
                "auth_primary": params["auth_primary"][idx], \
                "auth_speaker": params["auth_speaker"][idx], \
                "auth_focus": False }
        return author

    def _normaliseAuthorParams( self, params ):
        params["auth_id"]  = normaliseListParam( params.get("auth_id", []) )
        params["auth_title"]  = normaliseListParam( params.get("auth_title", []) )
        params["auth_firstName"]  = normaliseListParam( params.get("auth_firstName", []) )
        params["auth_surName"]  = normaliseListParam( params.get("auth_surName", []) )
        params["auth_affiliation"]       = normaliseListParam( params.get("auth_affiliation", []) )
        params["auth_email"]  = normaliseListParam( params.get("auth_email", []) )
        params["auth_phone"]  = normaliseListParam( params.get("auth_phone", []) )
        params["auth_address"]  = normaliseListParam( params.get("auth_address", []) )
        primaries  = normaliseListParam( params.get("auth_primary", []) )
        #params["auth_primary"] = normaliseListParam( params.get("auth_primary", []) )
        speakers = normaliseListParam( params.get("auth_speaker", []) )
        params["auth_primary"] = []
        params["auth_speaker"] = []
        for id in params["auth_id"]:
            params["auth_primary"].append( str(id) in primaries )
            params["auth_speaker"].append( str(id) in speakers)

    def _mapFromParams( self, params ):
        self._normaliseAuthorParams( params )
        self._primaryAuthors = IOBTree()
        self._secondaryAuthors = IOBTree()
        maxId = -1
        for idx in range( len( params["auth_id"] ) ):
            id = int( params["auth_id"][idx] )
            if id>maxId:
                maxId = id
            author = self._getAuthorFromParams( idx, params )
            if author["auth_primary"]:
                self._primaryAuthors[ id ] = author
            else:
                self._secondaryAuthors[ id ] = author
        self._nextId = maxId+1

    def getList( self ):
        res = []
        for a in self._primaryAuthors.values():
            res.append( a )
        for a in self._secondaryAuthors.values():
            res.append( a )
        return res

    def getPrimaryList( self ):
        return self._primaryAuthors.values()

    def getSecondaryList( self ):
        return self._secondaryAuthors.values()

    def _getNewAuthor( self, **data ):
        author = { "auth_id": int( self._nextId ), \
                "auth_title": data.get("title", ""), \
                "auth_firstName": data.get("firstName", ""), \
                "auth_surName": data.get("surName", ""), \
                "auth_affiliation": data.get("affiliation", ""), \
                "auth_email": data.get("email", ""), \
                "auth_phone": data.get("phone", ""), \
                "auth_address": data.get("address", ""), \
                "auth_primary": data.get("primary", False), \
                "auth_speaker": data.get("speaker", False), \
                "auth_focus": data.get("focus", False) }
        #self._authors[ self._nextId ] = author
        self._nextId += 1
        return author

    def addPrimaryAuthor( self, **data ):
        data["primary"] = True
        author = self._getNewAuthor( **data )
        self._primaryAuthors[ author["auth_id"] ] = author

    def addSecondaryAuthor( self, **data ):
        data["primary"] = False
        author = self._getNewAuthor( **data )
        self._secondaryAuthors[ author["auth_id"] ] = author

    def removePrimaryAuthor( self, id ):
        try:
            del self._primaryAuthors[ int(id) ]
        except KeyError:
            pass

    def removeSecondaryAuthor( self, id ):
        try:
            del self._secondaryAuthors[ int(id) ]
        except KeyError:
            pass


class AbstractData:

    def __init__( self, absMgr, params ):
        self._absMgr = absMgr
        self._afm = absMgr.getAbstractFieldsMgr()
        cparams = params.copy()
        self._mapFromParams( cparams )

    def _mapFromParams( self, params ):
        self.title = params.get("title",  "").strip()
        self._otherFields = {}
        for f in self._afm.getFields():
            id = f.getId()
            self._otherFields[id] = params.get("f_%s"%id,"").strip()
        self.type = params.get("type", None)
        self.tracks = normaliseListParam( params.get("tracks", []) )
        self.authors = _AbstractAuthorList( params )
        self.comments = params.get("comments","")

    def getFieldValue( self, id ):
        return self._otherFields.get(id, "")

    def setFieldValue( self, id, value ):
        self._otherFields[id] = value

    def check( self ):
        errors = []
        if self.title.strip() == "":
            errors.append( _("Abstract TITLE cannot be empty") )
        for f in self._afm.getFields():
            id = f.getId()
            caption = f.getCaption()
            ml = f.getMaxLength()
            if f.isMandatory() and self._otherFields.get(id,"") == "":
                errors.append(_("The field <b>%s</b> is mandatory") % caption)
            if ml != 0 and len(self._otherFields.get(id,"")) > ml:
                errors.append(_("The field <b>%s</b> cannot be more than %s characters") % (caption,ml))
        if len( self.authors.getPrimaryList() ) == 0:
            errors.append( _("No PRIMARY AUTHOR has been specified. You must define at least one primary author") )
        speakerCount = 0
        idx = 1
        for author in self.authors.getPrimaryList():
            if author["auth_firstName"].strip() == "":
                errors.append( _("FIRST NAME has not been specified for PRIMARY AUTHOR #%s")%idx )
            if author["auth_surName"].strip() == "":
                errors.append( _("SURNAME has not been specified for PRIMARY AUTHOR #%s")%idx )
            if author["auth_affiliation"].strip() == "":
                errors.append( _("AFFILIATION has not been specified for PRIMARY AUTHOR #%s")%idx )
            if author["auth_email"].strip() == "":
                errors.append( _("EMAIL has not been specified for PRIMARY AUTHOR #%s")%idx )
            if author["auth_speaker"]:
                speakerCount += 1
            idx += 1
        idx = 1
        for author in self.authors.getSecondaryList():
            if author["auth_firstName"].strip() == "":
                errors.append( _("FIRST NAME has not been specified for CO-AUTHOR #%s")%idx )
            if author["auth_surName"].strip() == "":
                errors.append( _("SURNAME has not been specified for CO-AUTHOR #%s")%idx )
            if author["auth_affiliation"].strip() == "":
                errors.append( _("AFFILIATION has not been specified for CO-AUTHOR #%s")%idx )
            if author["auth_speaker"]:
                speakerCount += 1
            idx += 1
        if speakerCount == 0:
            errors.append( _("At least ONE PRESENTER must be specified") )
        if not self.tracks and self._absMgr.areTracksMandatory():
            errors.append( _("At least ONE TRACK must be seleted") )
        return errors

    def toDict( self ):
        d = { "title": self.title, \
              "type": self.type, \
              "tracks": self.tracks, \
              "authors": self.authors, \
              "comments": self.comments }
        for f in self._afm.getFields():
            id = f.getId()
            d[id] = self._otherFields.get(id,"")
        return d


class _AbstractSubmissionNotification:

    def __init__( self, abstract ):
        self._abstract = abstract
        self._conf = self._abstract.getConference()
        self._subject=_("Abstract submission confirmation (%s)")%self._conf.getTitle()

    def getSubject( self ):
        return self._subject

    def setSubject(self,s):
        self._subject=s

    def getDestination( self ):
        return self._abstract.getSubmitter()

    def getFromAddr(self):
        return self._conf.getSupportEmail(returnNoReply=True)

    def getCCList(self):
        return self._abstract.getOwner().getSubmissionNotification().getCCList()

    def getToList(self):
        return self._abstract.getOwner().getSubmissionNotification().getToList()

    def getMsg( self ):
        primary_authors = []
        for auth in self._abstract.getPrimaryAuthorList():
            primary_authors.append("""%s (%s) <%s>"""%(auth.getFullName(), auth.getAffiliation(), auth.getEmail())  )
        co_authors = []
        for auth in self._abstract.getCoAuthorList():
            email = ""
            if auth.getEmail() != "":
                email = " <%s>"%auth.getEmail()
            co_authors.append( """%s (%s)%s"""%(auth.getFullName(), auth.getAffiliation(), email) )
        speakers = []
        for spk in self._abstract.getSpeakerList():
            speakers.append( spk.getFullName() )
        tracks = []
        for track in self._abstract.getTrackListSorted():
            tracks.append( """%s"""%track.getTitle() )
        tw = TextWrapper()
        msg = [ _("""_("Dear") %s,""")%self._abstract.getSubmitter().getStraightFullName() ]
        msg.append( "" )
        msg.append( tw.fill(_("The submission of your abstract has been successfully processed.")) )
        msg.append( "" )
        tw.break_long_words = False
        msg.append( tw.fill( _("""_("Abstract submitted"):\n<%s>.""")%urlHandlers.UHUserAbstracts.getURL( self._conf ) ) )
        msg.append( "" )
        msg.append( tw.fill( _("""_("Status of your abstract"):\n<%s>.""")%urlHandlers.UHAbstractDisplay.getURL( self._abstract ) ) )
        msg.append( "" )
        tw.subsequent_indent = ""
        msg.append( tw.fill( _("""_("See below a detailed summary of your submitted abstract"):""") ) )
        msg.append( "" )
        tw.subsequent_indent = " "*3
        msg.append( tw.fill( _("""_("Conference"): %s""")%self._conf.getTitle() ) )
        msg.append( "" )
        msg.append( tw.fill( _("""_("Submitted by"): %s""")%self._abstract.getSubmitter().getFullName() ) )
        msg.append( "" )
        msg.append( tw.fill( _("""_("Submitted on"): %s""")%self._abstract.getSubmissionDate().strftime( "%d %B %Y %H:%M" ) ) )
        msg.append( "" )
        msg.append( tw.fill( _("""_("Title"): %s""")%self._abstract.getTitle() ) )
        msg.append( "" )
        for f in self._conf.getAbstractMgr().getAbstractFieldsMgr().getFields():
            msg.append( tw.fill(f.getCaption()) )
            msg.append( self._abstract.getField(f.getId()) )
            msg.append( "" )
        msg.append( tw.fill( _("""_("Primary Authors"):""") ) )
        msg += primary_authors
        msg.append( "" )
        msg.append( tw.fill( _("""_("Co-authors"):""") ) )
        msg += co_authors
        msg.append( "" )
        msg.append( tw.fill( _("""_("Abstract presenters"):""") ) )
        msg += speakers
        msg.append( "" )
        msg.append( tw.fill( _("""_("Track classification"):""") ) )
        msg += tracks
        msg.append( "" )
        ctype= _("""--_("not specified")--""")
        if self._abstract.getContribType() is not None:
            ctype=self._abstract.getContribType().getName()
        msg.append( tw.fill( _("""_("Presentation type"): %s""")%ctype) )
        msg.append( "" )
        msg.append( tw.fill( _("""_("Comments"): %s""")%self._abstract.getComments() ) )
        msg.append( "" )
        return "\n".join( msg )

    def getBody(self):
        msg=self.getMsg()
        return _("""
_("The following email has been sent to %s"):

===

%s""")%(self.getDestination().getFullName(), msg)


class RHAbstractSubmission( RHAbstractSubmissionBase ):
    _uh = urlHandlers.UHAbstractSubmission

    def _checkParams( self, params ):
        RHAbstractSubmissionBase._checkParams( self, params )
        #if the user is not logged in we return inmediately as this form needs
        #   the user to be logged in and therefore all the checking below is not
        #   necessary

        if self._getUser() == None:
            return
        self._action = ""
        if "cancel" in params:
            self._action = "CANCEL"
            return
        id = params.get("type", "")
        params["type"] = self._conf.getContribTypeById(id)
        self._abstractData = AbstractData( self._target.getAbstractMgr(), params )
        if "add_primary_author" in params:
            #self._action = "NEW_AUTHOR"
            self._abstractData.authors.addPrimaryAuthor( focus=True )
        elif "add_secondary_author" in params:
            #self._action = "NEW_AUTHOR"
            self._abstractData.authors.addSecondaryAuthor( focus=True )
        elif "remove_primary_authors" in params:
            tmp = self._normaliseListParam( params.get("selected_primary_authors", []) )
            for id in tmp:
                self._abstractData.authors.removePrimaryAuthor( id )
        elif "remove_secondary_authors" in params:
            tmp = self._normaliseListParam( params.get("selected_secondary_authors", []) )
            for id in tmp:
                self._abstractData.authors.removeSecondaryAuthor( id )
        elif "validate" in params:
            self._action = "VALIDATE"
        else:
            #First call
            av = self._getUser()
            self._abstractData.authors.addPrimaryAuthor( \
                                        title = av.getTitle(), \
                                        firstName = av.getName(), \
                                        surName = av.getSurName(), \
                                        affiliation = av.getOrganisation(), \
                                        email = av.getEmail(), \
                                        phone = av.getTelephone(), \
                                        address = av.getAddress(), \
                                        speaker = True )

    def _doValidate( self ):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = abstracts.WPAbstractSubmission( self, self._target )
            pars = self._abstractData.toDict()
            pars["errors"] = errors
            pars["action"] = self._action
            return p.display( **pars )
        #Then, we create the abstract object and set its data to the one
        #   received
        cfaMgr = self._target.getAbstractMgr()
        afm = cfaMgr.getAbstractFieldsMgr()
        a = cfaMgr.newAbstract( self._getUser() )
        a.setTitle( self._abstractData.title )
        for f in afm.getFields():
            id = f.getId()
            a.setField(id, self._abstractData.getFieldValue(id))
        for authData in self._abstractData.authors.getPrimaryList():
            auth=a.newPrimaryAuthor(title = authData["auth_title"], \
                                firstName = authData["auth_firstName"], \
                                surName = authData["auth_surName"], \
                                email = authData["auth_email"], \
                                affiliation = authData["auth_affiliation"], \
                                address = authData["auth_address"], \
                                telephone = authData["auth_phone"] )
            if authData["auth_speaker"]:
                a.addSpeaker( auth )
        for authData in self._abstractData.authors.getSecondaryList():
            auth=a.newCoAuthor(title = authData["auth_title"], \
                                firstName = authData["auth_firstName"], \
                                surName = authData["auth_surName"], \
                                email = authData["auth_email"], \
                                affiliation = authData["auth_affiliation"], \
                                address = authData["auth_address"], \
                                telephone = authData["auth_phone"] )
            if authData["auth_speaker"]:
                a.addSpeaker( auth )
        a.setContribType( self._abstractData.type )
        for trackId in self._abstractData.tracks:
            track = self._conf.getTrackById( trackId )
            a.addTrack( track )
        a.setComments(self._abstractData.comments)


        #The commit must be forced before sending the confirmation
        DBMgr.getInstance().commit()
        #Email confirmation about the submission
        mail.Mailer.send( _AbstractSubmissionNotification( a ), self._conf.getSupportEmail(returnNoReply=True) )
        #Email confirmation about the submission to coordinators
        if cfaMgr.getSubmissionNotification().hasDestination():
            asn=_AbstractSubmissionNotification( a )
            asn.setSubject(_("[Indico] New abstract submission: %s")%asn.getDestination().getFullName())
            mail.GenericMailer.send( asn )
        #We must perform some actions: email warning to the authors
        #Finally, we display a confirmation form
        self._redirect( urlHandlers.UHAbstractSubmissionConfirmation.getURL( a ) )

    def _processIfOpened( self ):
        if self._action == "CANCEL":
            self._redirect( urlHandlers.UHConferenceCFA.getURL( self._conf ) )
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            p = abstracts.WPAbstractSubmission( self, self._target )
            pars = self._abstractData.toDict()
            return p.display( **pars )



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

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._conf).getDisplayTZ()
        filename = "%s - Abstract.pdf"%self._target.getTitle()
        pdf = AbstractToPDF(self._conf, self._target,tz=tz)
        data = pdf.getPDFBin()
        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractsDisplayPDF(RHConferenceBaseDisplay):

    def _checkProtection( self ):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("The Call For Abstracts was disabled by the conference managers"))

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._conf).getDisplayTZ()
        filename = "Abstracts.pdf"
        if not self._abstractIds:
            return _("No abstract to print")
        pdf = AbstractsToPDF(self._conf, self._abstractIds,tz=tz)
        data = pdf.getPDFBin()
        self._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractModificationBase( RHAbstractDisplayBase, RHModificationBaseProtected ):

    def _checkProtection( self ):
        RHModificationBaseProtected._checkProtection( self )


    def _processIfActive( self ):
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
            p = abstracts.WPCFANotYetOpened( self, self._conf )
            return p.display()
        #elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() :
        elif timezoneUtils.nowutc() > cfaMgr.getEndSubmissionDate() and timezoneUtils.nowutc() > modifDeadLine:
            p = abstracts.WPCFAClosed( self, self._conf )
            return p.display()
        else:
            return self._processIfOpened()


class RHAbstractModify( RHAbstractModificationBase ):
    _uh = urlHandlers.UHAbstractModify

    def _checkParams( self, params ):
        RHAbstractModificationBase._checkParams( self, params )
        #if the user is not logged in we return inmediately as this form needs
        #   the user to be logged in and therefore all the checking below is not
        #   necessary
        if self._getUser() == None:
            return
        self._action = ""
        if "cancel" in params:
            self._action = "CANCEL"
            return
        params["type"]=self._conf.getContribTypeById(params.get("type", ""))
        self._abstractData = AbstractData( self._conf.getAbstractMgr(), params )
        if "add_primary_author" in params:
            self._abstractData.authors.addPrimaryAuthor( focus=True )
        elif "add_secondary_author" in params:
            self._abstractData.authors.addSecondaryAuthor( focus=True )
        elif "remove_primary_authors" in params:
            tmp = self._normaliseListParam( params.get("selected_primary_authors", []) )
            for id in tmp:
                self._abstractData.authors.removePrimaryAuthor( id )
        elif "remove_secondary_authors" in params:
            tmp = self._normaliseListParam( params.get("selected_secondary_authors", []) )
            for id in tmp:
                self._abstractData.authors.removeSecondaryAuthor( id )
        elif "validate" in params:
            self._action = "VALIDATE"
        else:
            #First call
            afm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
            self._abstractData.title = self._abstract.getTitle()
            for f in afm.getFields():
                id = f.getId()
                self._abstractData.setFieldValue(id, self._abstract.getField(id))
            for author in self._abstract.getPrimaryAuthorList():
                data = { "title": author.getTitle(), \
                        "firstName": author.getFirstName(), \
                        "surName": author.getSurName(), \
                        "affiliation": author.getAffiliation(), \
                        "email": author.getEmail(), \
                        "phone": author.getTelephone(), \
                        "address": author.getAddress(), \
                        "primary": self._abstract.isPrimaryAuthor( author ), \
                        "speaker": self._abstract.isSpeaker( author ) }
                self._abstractData.authors.addPrimaryAuthor( **data )
            for author in self._abstract.getCoAuthorList():
                data = { "title": author.getTitle(), \
                        "firstName": author.getFirstName(), \
                        "surName": author.getSurName(), \
                        "affiliation": author.getAffiliation(), \
                        "email": author.getEmail(), \
                        "phone": author.getTelephone(), \
                        "address": author.getAddress(), \
                        "primary": self._abstract.isPrimaryAuthor( author ), \
                        "speaker": self._abstract.isSpeaker( author ) }
                self._abstractData.authors.addSecondaryAuthor( **data )
            self._abstractData.type=self._abstract.getContribType()
            trackIds = []
            for track in self._abstract.getTrackListSorted():
                trackIds.append( track.getId() )
            self._abstractData.tracks = trackIds
            self._abstractData.comments = self._abstract.getComments()

    def _doValidate( self ):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = abstracts.WPAbstractModify( self, self._target )
            pars = self._abstractData.toDict()
            pars["errors"] = errors
            pars["action"] = self._action
            return p.display( **pars )
        #Then, we create the abstract object and set its data to the one
        #   received
        self._abstract.setTitle( self._abstractData.title )
        afm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getFields():
            id = f.getId()
            self._abstract.setField( id, self._abstractData.getFieldValue(id))
        self._abstract.clearAuthors()
        #for authData in self._abstractData.authors.getList():
        #    auth = self._abstract.newAuthor( title = authData["auth_title"], \
        #                        firstName = authData["auth_firstName"], \
        #                        surName = authData["auth_surName"], \
        #                        email = authData["auth_email"], \
        #                        affiliation = authData["auth_affiliation"], \
        #                        address = authData["auth_address"], \
        #                        telephone = authData["auth_phone"] )
        #    if authData["auth_speaker"]:
        #        self._abstract.addSpeaker( auth )
        #    if authData["auth_primary"]:
        #        self._abstract.addPrimaryAuthor( auth )
        for authData in self._abstractData.authors.getPrimaryList():
            auth=self._abstract.newPrimaryAuthor(title=authData["auth_title"], \
                                firstName = authData["auth_firstName"], \
                                surName = authData["auth_surName"], \
                                email = authData["auth_email"], \
                                affiliation = authData["auth_affiliation"], \
                                address = authData["auth_address"], \
                                telephone = authData["auth_phone"] )
            if authData["auth_speaker"]:
                self._abstract.addSpeaker( auth )
        for authData in self._abstractData.authors.getSecondaryList():
            auth=self._abstract.newCoAuthor(title=authData["auth_title"], \
                                firstName = authData["auth_firstName"], \
                                surName = authData["auth_surName"], \
                                email = authData["auth_email"], \
                                affiliation = authData["auth_affiliation"], \
                                address = authData["auth_address"], \
                                telephone = authData["auth_phone"] )
            if authData["auth_speaker"]:
                self._abstract.addSpeaker( auth )
        self._abstract.setContribType( self._abstractData.type )
        #self._abstract.clearTracks()
        tracks = []
        for trackId in self._abstractData.tracks:
            tracks.append( self._conf.getTrackById( trackId ) )
        self._abstract.setTracks( tracks )
        self._abstract.setComments(self._abstractData.comments)
        #We must perform some actions: email warning to the authors
        #Finally, we display a confirmation form
        self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )

    def _processIfOpened( self ):
        #check if the modification period is not over or if the abstract
        #   is in a different status than Submitted
        if not self._conf.getAbstractMgr().inModificationPeriod() or \
                not isinstance( self._abstract.getCurrentStatus(), \
                                                AbstractStatusSubmitted ):
            wp = abstracts.WPAbstractCannotBeModified( self, self._abstract )
            return wp.display()
        if self._action == "CANCEL":
            self._redirect( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) )
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            p = abstracts.WPAbstractModify( self, self._target )
            pars = self._abstractData.toDict()
            pars["action"] = self._action
            return p.display( **pars )


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
