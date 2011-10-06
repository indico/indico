
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
from datetime import timedelta,datetime, time
import os, re, sys
import MaKaC.common.info as info
import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.conferenceBase as conferenceBase
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.abstracts as abstracts
import MaKaC.webinterface.pages.authors as authors
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.internalPagesMgr as internalPagesMgr
import MaKaC.user as user
import MaKaC.webinterface.mail as mail
from MaKaC.webinterface.pages.errors import WPAccessError, WPError404
import MaKaC.conference as conference
from MaKaC.common import Config, DBMgr
from MaKaC.common.utils import isStringHTML,sortContributionByDate
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.base import RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.errors import MaKaCError, ModificationError, NoReportError, AccessError, KeyAccessError, NotFoundError
from MaKaC.PDFinterface.conference import TimeTablePlain,AbstractBook, SimplifiedTimeTablePlain, ProgrammeToPDF, TimetablePDFFormat
from xml.sax.saxutils import escape
from MaKaC.participant import Participant
from MaKaC.ICALinterface.conference import ConferenceToiCal
from MaKaC.common.contribPacker import ConferencePacker, ZIPFileHandler
import StringIO, zipfile
from MaKaC.i18n import _

import MaKaC.common.timezoneUtils as timezoneUtils
from reportlab.platypus.doctemplate import LayoutError
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename

class RHConfSignIn( conferenceBase.RHConferenceBase ):

    _tohttps = True

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams( self, params )
        self._login = params.get( "login", "" ).strip()
        self._password = params.get( "password", "" ).strip()
        self._returnURL = params.get( "returnURL", "").strip()
        if self._returnURL == "":
            self._returnURL = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        self._loginURL = params.get( "loginURL", "").strip()
        self._signIn = params.get("signIn", "").strip()


    def _process( self ):
        #Check for automatic login
        auth = AuthenticatorMgr()
        av = auth.autoLogin(self)
        if av:
            url = self._returnURL
            self._getSession().setUser( av )
            if Config.getInstance().getBaseSecureURL().startswith('https://'):
                url = str(url).replace('http://', 'https://')
            self._redirect( url )
        if not self._signIn:
            p = conferences.WPConfSignIn( self, self._conf )
            return p.display( returnURL = self._returnURL )
        else:
            li = user.LoginInfo( self._login, self._password )
            av = auth.getAvatar(li)
            if not av:
                p = conferences.WPConfSignIn( self, self._conf, login = self._login, msg = "Wrong login or password" )
                return p.display( returnURL = self._returnURL )
            elif not av.isActivated():
                if av.isDisabled():
                    self._redirect(urlHandlers.UHConfDisabledAccount.getURL(self._conf, av))
                else:
                    self._redirect(urlHandlers.UHConfUnactivatedAccount.getURL( self._conf, av))
                return "your account is not active\nPlease activate it and retry"
            else:
                url = self._returnURL
                self._getSession().setUser( av )
                tzUtil = timezoneUtils.SessionTZ(av)
                tz = tzUtil.getSessionTZ()
                self._getSession().setVar("ActiveTimezone",tz)
            if Config.getInstance().getBaseSecureURL().startswith('https://'):
                url = str(url).replace('http://', 'https://')
            self._redirect( url )

# REPLACED BY RHSignOut IN login.py
#class RHConfSignOut( conferenceBase.RHConferenceBase ):
#
#    def _process( self ):
#        if self._getUser():
#            self._getSession().setUser( None )
#            self._setUser( None )
#        self._redirect( urlHandlers.UHConferenceDisplay.getURL( self._conf ) )



class RHConferenceAccessKey( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )
        self._accesskey = params.get( "accessKey", "" ).strip()

    def _process( self ):
        access_keys = self._getSession().getVar("accessKeys")
        if access_keys == None:
            access_keys = {}
        access_keys[self._conf.getUniqueId()] = self._accesskey
        self._getSession().setVar("accessKeys",access_keys)
        url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        self._redirect( url )


class RHConferenceForceAccessKey( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )

    def _process( self ):
        wp = WPAccessError( self )
        return wp.display()


class RHConfDisabledAccount( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = user.AvatarHolder().getById( self._userId )
        p = conferences.WPConfAccountDisabled( self, self._conf, av )
        return p.display()


class RHConfUnactivatedAccount( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = user.AvatarHolder().getById(self._userId)
        p = conferences.WPConfUnactivatedAccount( self, self._conf, av )
        return p.display()


class RHConfSendActivation( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()

    def _process( self ):
        av = user.AvatarHolder().getById(self._userId)
        sm = mail.sendConfirmationRequest(av)
        sm.send()
        self._redirect( urlHandlers.UHConfSignIn.getURL( self._conf ) )


class _UserUtils:

    def setUserData( self, a, userData):
        a.setName( userData["name"] )
        a.setSurName( userData["surName"] )
        a.setTitle( userData["title"] )
        a.setOrganisation( userData["organisation"] )
        a.setAddress( userData["address"] )
        a.setEmail( userData["email"] )
        a.setTelephone( userData["telephone"] )
        a.setFax( userData["fax"] )
        ##################################
        # Fermi timezone awareness       #
        ##################################
        a.setTimezone(userData["timezone"])
        a.setDisplayTZMode(userData["displayTZMode"])
        ##################################
        # Fermi timezone awareness(end)  #
        ##################################
    setUserData = classmethod( setUserData )


class RHConfUserCreation( conferenceBase.RHConferenceBase ):
    _uh = urlHandlers.UHConfUserCreation

    def _checkProtection( self ):
        pass

    def _checkParams( self, params ):
        self._params = params
        conferenceBase.RHConferenceBase._checkParams( self, params )
        self._save = params.get("Save", "")
        self._returnURL = params.get( "returnURL", "").strip()

    def _process( self ):
        save = False
        ih = AuthenticatorMgr()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        self._params["msg"] = ""
        if self._save:
            save = True
            #check submited data
            if not self._params.get("name",""):
                self._params["msg"] += _("You must enter a name.")+"<br>"
                save = False
            if not self._params.get("surName",""):
                self._params["msg"] += _("You must enter a surname.")+"<br>"
                save = False
            if not self._params.get("organisation",""):
                self._params["msg"] += _("You must enter the name of your organisation.")+"<br>"
                save = False
            if not self._params.get("email",""):
                self._params["msg"] += _("You must enter an email address.")+"<br>"
                save = False
            if not self._params.get("login",""):
                self._params["msg"] += _("You must enter a login.")+"<br>"
                save = False
            if not self._params.get("password",""):
                self._params["msg"] += _("You must define a password.")+"<br>"
                save = False
            if self._params.get("password","") != self._params.get("passwordBis",""):
                self._params["msg"] += _("You must enter the same password twice.")+"<br>"
                save = False
            if not ih.isLoginFree(self._params.get("login","")):
                self._params["msg"] += _("Sorry, the login you requested is already in use. Please choose another one.")+"<br>"
                save = False
            if not self._validMail(self._params.get("email","")):
                self._params["msg"] += _("You must enter a valid email address")
                save = False
        if save:
            #Data are OK, Now check if there is an existing user or create a new one
            ah = user.AvatarHolder()
            res =  ah.match({"email": self._params["email"]}, exact=1, forceWithoutExtAuth=True)
            if res:
                #we find a user with the same email
                a = res[0]
                #check if the user have an identity:
                if a.getIdentityList():
                    self._redirect( urlHandlers.UHConfUserExistWithIdentity.getURL( self._conf, a))
                    return
                else:
                    #create the identity to the user and send the comfirmatio email
                    li = user.LoginInfo( self._params["login"], self._params["password"] )
                    id = ih.createIdentity( li, a, "Local" )
                    ih.add( id )
                    DBMgr.getInstance().commit()
                    if minfo.getModerateAccountCreation():
                        mail.sendAccountCreationModeration(a).send()
                    else:
                        mail.sendConfirmationRequest(a).send()
                        if minfo.getNotifyAccountCreation():
                            mail.sendAccountCreationNotification(a).send()
            else:
                a = user.Avatar()
                _UserUtils.setUserData( a, self._params )
                ah.add(a)
                li = user.LoginInfo( self._params["login"], self._params["password"] )
                id = ih.createIdentity( li, a, "Local" )
                ih.add( id )
                DBMgr.getInstance().commit()
                if minfo.getModerateAccountCreation():
                    mail.sendAccountCreationModeration(a).send()
                else:
                    mail.sendConfirmationRequest(a).send()
                    if minfo.getNotifyAccountCreation():
                        mail.sendAccountCreationNotification(a).send()
            self._redirect( urlHandlers.UHConfUserCreated.getURL( self._conf, a ) )
        else:
            p = conferences.WPConfUserCreation( self, self._conf, self._params )
            return p.display()

    def _validMail(self,email):
        if re.search("^[a-zA-Z][\w\.-]*[a-zA-Z0-9]@[a-zA-Z0-9][\w\.-]*[a-zA-Z0-9]\.[a-zA-Z][a-zA-Z\.]*[a-zA-Z]$",email):
            return True
        return False

class RHConfUserCreated( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams( self, params )
        self._av = user.AvatarHolder().getById(params["userId"])

    def _process( self ):
        p = conferences.WPConfUserCreated( self, self._conf, self._av )
        return p.display()


class RHConfActivate( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams(self, params )
        self._userId = params.get( "userId", "" ).strip()
        self._key = params.get( "key", "" ).strip()
        self._returnURL = params.get( "returnURL", "").strip()


    def _process( self ):
        av = user.AvatarHolder().getById(self._userId)
        if av.isActivated():
            p = conferences.WPConfAccountAlreadyActivated( self, self._conf, av )
            return p.display()
            #return "your account is already activated"
        if av.isDisabled():
            p = conferences.WPConfAccountDisabled( self, self._conf, av )
            return p.display()
            #return "your account is disabled. please, ask to enable it"
        elif self._key == av.getKey():
            av.activateAccount()
            p = conferences.WPConfAccountActivated( self, self._conf, av, self._returnURL )
            return p.display()
            #return "Your account is activate now"
        else:
            return "Wrong key. Please, ask for a new one"


class RHConfUserExistWithIdentity( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams( self, params )
        self._av = user.AvatarHolder().getById(params["userId"])

    def _process( self ):
        p = conferences.WPConfUserExistWithIdentity( self, self._conf, self._av )
        return p.display()


class RHConfSendLogin( conferenceBase.RHConferenceBase ):

    def _checkParams( self, params ):
        conferenceBase.RHConferenceBase._checkParams( self, params )
        self._userId = params.get( "userId", "" ).strip()
        self._email = params.get("email", "").strip()

    def _process( self ):
        av = None
        if self._userId != "":
            av = user.AvatarHolder().getById(self._userId)
        elif self._email != "":
            try:
                av = user.AvatarHolder().match({"email":self._email})[0]
            except IndexError:
                pass
        if av:
            sm = mail.sendLoginInfo(av)
            sm.send()
        self._redirect(urlHandlers.UHConfSignIn.getURL( self._conf ))


class RHConferenceBaseDisplay( RHConferenceBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

    def _checkProtection( self ):

        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin, RCCollaborationPluginAdmin
        if not RCCollaborationAdmin.hasRights(self, None) and \
            not RCCollaborationPluginAdmin.hasRights(self, plugins = "any"):
            RHDisplayBaseProtected._checkProtection( self )


class RHConferenceDisplay( RoomBookingDBMixin, RHConferenceBaseDisplay ):
    _uh = urlHandlers.UHConferenceDisplay

    def _process( self ):
        params = self._getRequestParams()
        #set default variables
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"
        #get default/selected view
        view = "static"
        wf = self.getWebFactory()
        if wf != None:
            type = self.getWebFactory().getId()
        else:
            type = "conference"
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._reqParams.has_key("view"):
            view = self._reqParams["view"]
        else:
            view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
            # if no default view was attributed, then get the configuration default
            if view == "" or not styleMgr.existsStyle(view):
                view =styleMgr.getDefaultStyleForEventType( type )
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).setDefaultStyle( view )
        isLibxml = True
        warningText = ""
        try:
            import lxml
        except:
            isLibxml = False

        # create the html factory
        if type == "conference":
            if params.get("ovw", False):
                p = conferences.WPConferenceDisplay( self, self._target )
            else:
                self._page = None
                intPagesMgr=internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._target)
                for page in intPagesMgr.getPagesList():
                    if page.isHome():
                        self._page = page
                if not self._page:
                    p = conferences.WPConferenceDisplay( self, self._target )
                else:
                    p = conferences.WPInternalPageDisplay(self,self._target, self._page)
        elif view in styleMgr.getXSLStyles():
            if not isLibxml:
                warningText = "lxml needs to be installed if you want to use a stylesheet-driven display - switching to static display"
            self._req.content_type = "text/xml"
            p = conferences.WPXSLConferenceDisplay( self, self._target, view, type, self._reqParams )
        elif view != "static":
            p = conferences.WPTPLConferenceDisplay( self, self._target, view, type, self._reqParams )
        else:
            if wf != None:
                p = wf.getConferenceDisplayPage( self, self._target, self._reqParams )
            else:
                p = conferences.WPConferenceDisplay( self, self._target )
        # generate the html

        return warningText + p.display(**params)


class RHConferenceOtherViews( RoomBookingDBMixin, RHConferenceBaseDisplay ):
    """this class is for the conference type objects only
    it is an alternative to the standard TimeTable view"""
    _uh = urlHandlers.UHConferenceOtherViews

    def _process( self ):
        #set default variables
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"
        #get default/selected view
        view = "standard"
        type = "conference"
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        isLibxml = True
        try:
            import lxml
        except:
            isLibxml = False
        if self._reqParams.has_key("view"):
            view = self._reqParams["view"]
        else:
            view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
            # if no default view was attributed, then get the configuration default
            if view == "":
                view =styleMgr.getDefaultStyleForEventType( type )
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).setDefaultStyle( view )
        # create the html factory
        if view in styleMgr.getXSLStyles() and isLibxml:
            p = conferences.WPXSLConferenceDisplay( self, self._target, view, type, self._reqParams )
        elif view != "static":
            p = conferences.WPTPLConferenceDisplay( self, self._target, view, type, self._reqParams )
        else:
            p = conferences.WPMeetingTimeTable( self, self._target,"parallel","meeting",self._reqParams )
        # generate the html
        if view == "xml" and self._reqParams.get('fr') == 'no':
            self._req.content_type = "text/xml"
        return p.display()


class RHConferenceGetLogo(RHConferenceBaseDisplay):

    def _process(self):
        logo=self._target.getLogo()
        self._req.headers_out["Content-Length"]="%s"%logo.getSize()
        cfg=Config.getInstance()
        mimetype=cfg.getFileTypeMimeType(logo.getFileType())
        self._req.content_type="""%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%cleanHTMLHeaderFilename(logo.getFileName())
        return self._target.getLogo().readBin()


class RHConferenceGetCSS(RHConferenceBaseDisplay):

    """
    CSS which is used just for a conference.
    """

    def _process(self):
        sm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        css=sm.getLocalCSS()
        if css:
            self._req.headers_out["Content-Length"]="%s"%css.getSize()
            self._req.content_type="text/css"
            self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%css.getFileName()
            return css.readBin()

        return ""


class RHConferenceGetPic(RHConferenceBaseDisplay):

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._picId = params.get("picId","")

    def _process(self):
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        if im.getPic(self._picId):
            pic=im.getPic(self._picId).getLocalFile()
            self._req.headers_out["Content-Length"]="%s"%pic.getSize()
            cfg=Config.getInstance()
            mimetype=cfg.getFileTypeMimeType(pic.getFileType())
            self._req.content_type="""%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%pic.getFileName()
            return pic.readBin()
        else:
            from indico.web.wsgi import webinterface_handler_config as apache
            self._req.status = apache.HTTP_NOT_FOUND
            return WPError404(self, urlHandlers.UHConferenceDisplay.getURL(self._conf)).display()


class RHConferenceEmail(RHConferenceBaseDisplay, base.RHProtected):
    _uh = urlHandlers.UHConferenceEmail

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._auth = params.has_key("authId")
        self._chair = params.has_key("chairId")
        if params.has_key("contribId"):
            contrib = self._conf.getContributionById(params.get("contribId",""))
        if self._chair:
            chairid=params.get("chairId","")
            chair = self._conf.getChairById(chairid)
            if chair == None:
                raise NotFoundError(_("The chair you try to email does not exist."))
            self._emailto = chair
        if self._auth:
            authid=params.get("authId","")
            if not contrib:
                raise MaKaCError(_("The author's contribution does not exist anymore."))
            author = contrib.getAuthorById(authid)
            if author == None:
                raise NotFoundError(_("The author you try to email does not exist."))
            self._emailto = author

    def _process(self):
        postURL = urlHandlers.UHConferenceSendEmail.getURL(self._emailto)
        p=conferences.WPEMail(self, self._target)
        return p.display(emailto=[self._emailto], postURL=postURL)

class RHConferenceSendEmail (RHConferenceBaseDisplay, base.RHProtected):
    _uh = urlHandlers.UHConferenceSendEmail

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams( self, params )
        if params.has_key("contribId"):
            contrib = self._conf.getContributionById(params.get("contribId",""))
        if params.has_key("chairId"):
            chairid=params.get("chairId","")
            self._to = self._conf.getChairById(chairid).getEmail()
        if params.has_key("authId"):
            authid=params.get("authId","")
            self._to = contrib.getAuthorById(authid).getEmail()
        fromId = params.get("from","")
        self._from = (user.AvatarHolder()).getById(fromId).getEmail()
        self._cc = self._from
        self._subject=params.get("subject","")
        self._body = params.get("body","")
        self._send = params.has_key("OK")

    def _process(self):
        if self._send:
            mail.personMail.send(self._to, self._cc, self._from,self._subject,self._body)
            p = conferences.WPSentEmail(self, self._target)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(self._conf))



class RHConferenceProgram( RHConferenceBaseDisplay ):
    _uh = urlHandlers.UHConferenceProgram

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._xs = self._normaliseListParam( params.get("xs", []) )


    def _process( self ):
        p = conferences.WPConferenceProgram( self, self._target )
        return p.display( xs = self._xs )


class RHConferenceProgramPDF( RHConferenceBaseDisplay ):

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._target).getDisplayTZ()
        filename = "%s - Programme.pdf"%cleanHTMLHeaderFilename(self._target.getTitle())
        from MaKaC.PDFinterface.conference import ProgrammeToPDF
        pdf = ProgrammeToPDF(self._target, tz=tz)
        data = pdf.getPDFBin()
        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        #self._req.content_type = """%s; name="%s\""""%(mimetype, filename )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data

class RHConferenceTimeTable( RoomBookingDBMixin, RHConferenceBaseDisplay ):
    _uh = urlHandlers.UHConferenceTimeTable

    def _process( self ):
        defStyle = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
        if defStyle in ["", "static", "parallel"]:
            p = conferences.WPConferenceTimeTable( self, self._target )
            return p.display( **self._getRequestParams() )
        else:
            url = urlHandlers.UHConferenceOtherViews.getURL( self._conf )
            url.addParam("view", defStyle)
            self._redirect(url)


class RHTimeTablePDF(RHConferenceTimeTable):

    fontsizes = ['xxx-small', 'xx-small', 'x-small', 'smaller', 'small', 'normal', 'large', 'larger']

    def _checkParams(self,params):
        RHConferenceTimeTable._checkParams(self,params)
        self._showSessions=self._normaliseListParam(params.get("showSessions",[]))
        if "all" in self._showSessions:
            self._showSessions.remove("all")
        self._showDays=self._normaliseListParam(params.get("showDays",[]))
        if "all" in self._showDays:
            self._showDays.remove("all")
        self._sortingCrit=None
        if params.has_key("sortBy") and params["sortBy"].strip()!="":
            self._sortingCrit=contribFilters.SortingCriteria([params.get( "sortBy", "number").strip()])
        self._pagesize = params.get('pagesize','A4')
        self._fontsize = params.get('fontsize','normal')
        try:
            self._firstPageNumber = int(params.get('firstPageNumber','1'))
        except ValueError:
            self._firstPageNumber = 1
        self._showSpeakerAffiliation = False
        if params.has_key("showSpeakerAffiliation"):
            self._showSpeakerAffiliation = True
        # Keep track of the used layout for getting back after cancelling
        # the export.
        self._view = params.get("view", displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle())

    def _reduceFontSize( self ):
        index = self.fontsizes.index(self._fontsize)
        if index > 0:
            self._fontsize = self.fontsizes[index-1]
            return True
        return False

    def _process(self):
        tz = timezoneUtils.DisplayTZ(self._aw,self._target).getDisplayTZ()
        params = self._getRequestParams()
        ttPDFFormat=TimetablePDFFormat(params)

        # Choose action depending on the button pressed
        if params.has_key("cancel"):
            # If the export is cancelled, redirect to the display
            # page
            url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
            url.addParam("view", self._view)
            self._redirect(url)
        else :
            retry = True
            while retry:
                if params.get("typeTT","normalTT")=="normalTT":
                    filename = "timetable.pdf"
                    pdf = TimeTablePlain(self._target,self.getAW(),
                            showSessions=self._showSessions,showDays=self._showDays,
                            sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
                            pagesize = self._pagesize, fontsize = self._fontsize,
                            firstPageNumber = self._firstPageNumber,
                            showSpeakerAffiliation = self._showSpeakerAffiliation)
                else:
                    filename = "SimplifiedTimetable.pdf"
                    pdf = SimplifiedTimeTablePlain(self._target,self.getAW(),
                        showSessions=self._showSessions,showDays=self._showDays,
                        sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
                        pagesize = self._pagesize, fontsize = self._fontsize)
                try:
                    data=pdf.getPDFBin()
                    retry = False
                except LayoutError, e:
                    if not self._reduceFontSize():
                        raise MaKaCError("Error in PDF generation - One of the paragraphs does not fit on a page")
                except Exception:
                    raise

    ##        tries = 5
    ##        while tries:
    ##            if params.get("typeTT","normalTT")=="normalTT":
    ##                filename = "timetable.pdf"
    ##                pdf = TimeTablePlain(self._target,self.getAW(),
    ##                        showSessions=self._showSessions,showDays=self._showDays,
    ##                        sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
    ##                        pagesize = self._pagesize, fontsize = self._fontsize, firstPageNumber = self._firstPageNumber, tz=tz)
    ##            else:
    ##                filename = "SimplifiedTimetable.pdf"
    ##                pdf = SimplifiedTimeTablePlain(self._target,self.getAW(),
    ##                    showSessions=self._showSessions,showDays=self._showDays,
    ##                    sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
    ##                    pagesize = self._pagesize, fontsize = self._fontsize, tz=tz)
    ##            try:
    ##                data=pdf.getPDFBin()
    ##                tries = 0
    ##            except LayoutError, e:
    ##                if self._reduceFontSize():
    ##                    tries -= 1
    ##                else:
    ##                    tries = 0
    ##                    raise MaKaCError(str(e))

            self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg=Config.getInstance()
            mimetype=cfg.getFileTypeMimeType("PDF")
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%filename
            return data

class RHTimeTableCustomizePDF(RHConferenceTimeTable):

    def _checkParams(self,params):
        RHConferenceTimeTable._checkParams(self,params)
        self._cancel = params.has_key("cancel")
        self._view = params.get("view", "standard")

    def _process(self):
        # TODO: why not construct p this way only if wf == None?
        p=conferences.WPTimeTableCustomizePDF(self, self._target)
        wf = self.getWebFactory()
        if wf != None:
            p=wf.getTimeTableCustomizePDF(self, self._target, self._view)
        return p.display(**self._getRequestParams())


class _HideWithdrawnFilterField(filters.FilterField):
    """
    """
    _id = "hide_withdrawn"

    def __init__(self,conf,values):
        pass

    def satisfies(self,contribution):
        """
        """
        return not isinstance(contribution.getCurrentStatus(),conference.ContribStatusWithdrawn)


class ContributionsFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        contribFilters.TypeFilterField.getId():contribFilters.TypeFilterField, \
        contribFilters.TrackFilterField.getId():contribFilters.TrackFilterField, \
        contribFilters.SessionFilterField.getId():contribFilters.SessionFilterField, \
        _HideWithdrawnFilterField.getId(): _HideWithdrawnFilterField
                }


class RHContributionList( RHConferenceBaseDisplay ):
    _uh = urlHandlers.UHContributionList

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        # Sorting
        self._sortingCrit=contribFilters.SortingCriteria( [params.get( "sortBy", "number").strip()] )
        self._order = params.get("order","down")
        # Filtering
        filterUsed = params.has_key( "OK" ) # this variable is true when the
                                            # filter has been used
        filter = {"hide_withdrawn": True}
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append( type.getId() )
        else:
            for id in self._normaliseListParam( params.get("selTypes", []) ):
                ltypes.append(id)
        filter["type"] = ltypes

        ltracks = []
        if not filterUsed:
            for track in self._conf.getTrackList():
                ltracks.append( track.getId() )
        filter["track"] = self._normaliseListParam( params.get("selTracks", ltracks) )

        lsessions = []
        if not filterUsed:
            for session in self._conf.getSessionList():
                lsessions.append( session.getId() )
        filter["session"] = self._normaliseListParam( params.get("selSessions", lsessions) )

        self._filterCrit=ContributionsFilterCrit(self._conf,filter)
        typeShowNoValue, trackShowNoValue, sessionShowNoValue = True, True, True
        if filterUsed:
            if self._conf.getContribTypeList():
                typeShowNoValue =  params.has_key("typeShowNoValue")
            if self._conf.getTrackList():
                trackShowNoValue =  params.has_key("trackShowNoValue")
            if self._conf.getSessionList():
                sessionShowNoValue =  params.has_key("sessionShowNoValue")
        self._filterCrit.getField("type").setShowNoValue( typeShowNoValue )
        self._filterCrit.getField("track").setShowNoValue( trackShowNoValue )
        self._filterCrit.getField("session").setShowNoValue( sessionShowNoValue )
        self._sc=params.get("sc",1)
        self._nc=params.get("nc",20)


    def _process( self ):
        p = conferences.WPContributionList( self, self._target )
        return p.display(sortingCrit = self._sortingCrit, filterCrit = self._filterCrit, sc=self._sc, nc=self._nc, order=self._order)


class RHAuthorIndex(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAuthorIndex

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._view=params.get("view","full")
        self._letter=params.get("letter","a")

    def _process(self):
        p=conferences.WPAuthorIndex(self,self._target)
        return p.display(viewMode=self._view,selLetter=self._letter)

class RHSpeakerIndex(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAuthorIndex

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._view=params.get("view","full")
        self._letter=params.get("letter","a")

    def _process(self):
        p=conferences.WPSpeakerIndex(self,self._target)
        return p.display(viewMode=self._view,selLetter=self._letter)

class RHMyStuff(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuff

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPMyStuff(self,self._target)
        return p.display()

class RHConfMyStuffMySessions(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMySessions

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        ls = set(self._conf.getCoordinatedSessions(self._aw.getUser())) | \
             set(self._conf.getManagedSession(self._aw.getUser()))
        if len(ls) == 1:
            self._redirect(urlHandlers.UHSessionModification.getURL(ls.pop()))
        else:
            p = conferences.WPConfMyStuffMySessions(self, self._target)
            return p.display()

class RHConfMyStuffMyContributions(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMyContributions

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPConfMyStuffMyContributions(self,self._target)
        return p.display()

class RHConfMyStuffMyTracks(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMyTracks

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        ltracks = self._target.getCoordinatedTracks(self._aw.getUser())

        if len(ltracks) == 1:
            self._redirect(urlHandlers.UHTrackModifAbstracts.getURL(ltracks[0]))
        else:
            p = conferences.WPConfMyStuffMyTracks(self, self._target)
            return p.display()


class RHContribsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        self._req = req

    def process(self, params):
        if params.has_key("PDF"):
            return RHContributionListToPDF(self._req).process(params)
        return "no action to do"

class RHContributionListToPDF(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            contrib = self._conf.getContributionById(id)
            if contrib.canAccess(self.getAW()):
                self._contribs.append(contrib)

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._conf).getDisplayTZ()
        filename = "Contributions.pdf"
        if not self._contribs:
            return "No contributions to print"
        from MaKaC.PDFinterface.conference import ConfManagerContribsToPDF
        pdf = ConfManagerContribsToPDF(self._conf, self._contribs, tz=tz)
        data = pdf.getPDFBin()
        self._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractBook(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAbstractBook

    def _checkProtection( self ):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("The Call For Abstracts was disabled by the conference managers"))

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._target).getDisplayTZ()
        filename = "%s - Book of abstracts.pdf"%cleanHTMLHeaderFilename(self._target.getTitle())
        pdf = AbstractBook(self._target,self.getAW(), tz=tz)
        data = pdf.getPDFBin()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data


class RHConfParticipantsNewPending(RHConferenceDisplay):
    _uh = urlHandlers.UHConfParticipantsNewPending

    def _process( self ):
        params = self._getRequestParams()

        errorList = []
        if self._conf.getStartDate() < timezoneUtils.nowutc() :
            errorList.append("This event began on %s"%self._conf.getStartDate())
            errorList.append("You cannot apply for participation after the event began")

        if not self._conf.getParticipation().isAllowedForApplying() :
            errorList.append("Participation in this event is restricted to persons invited")
            errorList.append("If you insist on taking part in this event, please contact the event manager")

        if errorList:
            self._reqParams["errorMsg"] = errorList
            return RHConferenceDisplay._process(self)

        params["formAction"] = str(urlHandlers.UHConfParticipantsAddPending.getURL(self._conf))
        user = self._getUser()
        if user is not None :
            params["titleValue"] = user.getTitle()
            params["surNameValue"] = user.getFamilyName()
            params["nameValue"] = user.getName()
            params["emailValue"] = user.getEmail()
            params["addressValue"] = user.getAddress()
            params["affiliationValue"] = user.getAffiliation()
            params["phoneValue"] = user.getTelephone()
            params["faxValue"] = user.getFax()

            params["disabledTitle"] = params["disabledSurName"] = True
            params["disabledName"] = params["disabledEmail"] = True
            params["disabledAddress"] = params["disabledPhone"] = True
            params["disabledFax"] = params["disabledAffiliation"] = True


        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfModifParticipantsNewPending(self, self._conf)
        else :
            p = conferences.WPConfModifParticipantsNewPending( self, self._target )
        return p.display(**params)


class RHConfParticipantsAddPending(RHConferenceDisplay):
    _uh = urlHandlers.UHConfParticipantsAddPending

    def _process( self ):
        params = self._getRequestParams()
        errorList = []
        infoList = []
        if params.has_key("ok") :
            user = self._getUser()
            pending = Participant(self._conf, user)
            if user is None :
                pending.setTitle(params.get("title",""))
                pending.setFamilyName(params.get("surName",""))
                pending.setFirstName(params.get("name",""))
                pending.setEmail(params.get("email",""))
                pending.setAffiliation(params.get("affiliation",""))
                pending.setAddress(params.get("address",""))
                pending.setTelephone(params.get("phone",""))
                pending.setFax(params.get("fax",""))
            participation = self._conf.getParticipation()
            if participation.alreadyParticipating(pending) != 0 or participation.alreadyPending(pending) != 0:
                errorList.append("There is already a participant with the email address '%s' in this meeting."
                                 % pending.getEmail())
            else:
                if participation.addPendingParticipant(pending):
                    if participation.getAutoAccept():
                        infoList.append(_("The request for participation has been accepted"))
                    else:
                        infoList.append("The participant identified by email '%s' has been added to the list of pending participants"
                                    % pending.getEmail())
                else:
                    errorList.append(_("The participant cannot be added."))

        if infoList:
            self._reqParams["infoMsg"] = infoList
        if errorList:
            self._reqParams["errorMsg"] = errorList

        return RHConferenceDisplay._process(self)


class RHConfParticipantsRefusal(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConfParticipantsRefusal

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        participantId = params["participantId"]
        if self._cancel:
            participant = self._conf.getParticipation().getParticipantById(participantId)
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        elif self._confirm:
            participant = self._conf.getParticipation().getParticipantById(participantId)
            participant.setStatusRefused()
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        else:
            return conferences.WPConfModifParticipantsRefuse( self, self._conf ).display(**params)


class RHConfParticipantsInvitation(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConfParticipantsInvitation

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        participantId = params["participantId"]
        if self._cancel:
            participant = self._conf.getParticipation().getParticipantById(participantId)
            if participant == None:
                raise NoReportError("It seems you have been withdrawn from the list of invited participants")
            participant.setStatusRejected()
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        elif self._confirm:
            participant = self._conf.getParticipation().getParticipantById(participantId)
            if participant == None:
                raise NoReportError("It seems you have been withdrawn from the list of invited participants")
            participant.setStatusAccepted()
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        else:
            return conferences.WPConfModifParticipantsInvite( self, self._conf ).display(**params)

class RHConferenceToiCal(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._detailLevel = params.get("detailLevel","top")

    def _process( self ):
        filename = "%s - Event.ics"%cleanHTMLHeaderFilename(self._target.getTitle())
        ical = ConferenceToiCal(self._target.getConference())

        if self._detailLevel == "contributions":
            data = ical.getDetailedBody()
        else:
            data = ical.getBody()

        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ICAL" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data

class RHConferenceToXML(RoomBookingDBMixin, RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._xmltype = params.get("xmltype","standard")

    def _process( self ):
        filename = "%s - Event.xml"%cleanHTMLHeaderFilename(self._target.getTitle())
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("event")
        outgen.confToXML(self._target.getConference(),0,0,1)
        xmlgen.closeTag("event")
        data = xmlgen.getXml()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data


class RHConferenceToMarcXML(RHConferenceBaseDisplay):

    def _process( self ):
        filename = "%s - Event.xml"%cleanHTMLHeaderFilename(self._target.getTitle())
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.confToXMLMarc21(self._target.getConference())
        xmlgen.closeTag("marc:record")
        data = xmlgen.getXml()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data

class RHInternalPageDisplay(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHInternalPageDisplay

    def _checkParams(self,params):
        RHConferenceBaseDisplay._checkParams(self,params)
        if params.has_key("pageId"):
            pageId=params.get("pageId")
            intPagesMgr=internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._conf)
            self._page=intPagesMgr.getPageById(pageId)
            self._target = self._conf
            if self._page is None:
                raise MaKaCError( _("The webpage, you are trying to access, does not exist"))
        else:
            raise MaKaCError( _("The webpage, you are trying to access, does not exist"))

    def getCurrentURL( self ):
        return self._uh.getURL( self._page )

    def _process( self ):
        p=conferences.WPInternalPageDisplay(self,self._conf, self._page)
        return p.display()

class RHConferenceLatexPackage(RHConferenceBaseDisplay):

    def _process( self ):
        #return "nothing"
        filename = "%s-BookOfAbstracts.zip"%cleanHTMLHeaderFilename(self._target.getTitle())
        zipdata = StringIO.StringIO()
        zip = zipfile.ZipFile(zipdata, "w")
        for cont in self._target.getContributionList():
            f = []
            f.append("""\\section*{%s}"""%cont.getTitle())
            f.append(" ")
            l = []
            affil = {}
            i = 1
            for pa in cont.getPrimaryAuthorList():
                if pa.getAffiliation() in affil.keys():
                    num = affil[pa.getAffiliation()]
                else:
                    affil[pa.getAffiliation()] = i
                    num = i
                    i += 1

                l.append("""\\noindent \\underline{%s}$^%d$"""%(pa.getFullName(), num))

            for ca in cont.getCoAuthorList():
                if ca.getAffiliation() in affil.keys():
                    num = affil[ca.getAffiliation()]
                else:
                    affil[ca.getAffiliation()] = i
                    num = i
                    i += 1
                l.append("""%s$^%d$"""%(ca.getFullName(), num))

            f.append(",\n".join(l))
            f.append("\n")
            l = []
            for key in affil.keys():
                l.append("""$^%d$%s"""%(affil[key], key))
            f.append("\\noindent " + ",\n".join(l))
            f.append("\n")
            f.append("""\\noindent %s"""%cont.getDescription())
            zip.writestr("contribution-%s"%cont.getId(), "\n".join(f))
        zip.close()
        data = zipdata.getvalue()
        zipdata.close()

        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ZIP" )
        #self._req.content_type = """%s; name="%s\""""%(mimetype, filename )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename.replace("\r\n"," ")
        return data


class RHFullMaterialPackage(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConferenceDisplayMaterialPackage

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._errors = params.get("errors","")

    def _process( self ):

        wf = self.getWebFactory()
        if wf!=None : #Event == Meeting/Lecture
            p = wf.getDisplayFullMaterialPackage(self,self._target)
        else : #Event == Conference
            p = conferences.WPDisplayFullMaterialPackage(self,self._target)
        return p.display(errors=self._errors)




class RHFullMaterialPackagePerform(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConferenceDisplayMaterialPackagePerform

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._days=self._normaliseListParam(params.get("days",[]))
        self._mainResource = (params.get("mainResource","") != "")
        self._fromDate = ""
        fromDay = params.get("fromDay","")
        fromMonth = params.get("fromMonth","")
        fromYear = params.get("fromYear","")
        if fromDay != "" and fromMonth != "" and fromYear != "" and \
           fromDay != "dd" and fromMonth != "mm" and fromYear != "yyyy":
            self._fromDate = "%s %s %s"%(fromDay, fromMonth, fromYear)
        self._cancel = params.has_key("cancel")
        self._materialTypes=self._normaliseListParam(params.get("materialType",[]))
        self._sessionList = self._normaliseListParam(params.get("sessionList",[]))

    def _process( self ):
        if not self._cancel:
            if self._materialTypes != []:
                p=ConferencePacker(self._conf, self._aw)
                path=p.pack(self._materialTypes, self._days, self._mainResource, self._fromDate, ZIPFileHandler(),self._sessionList)
                if not p.getItems():
                    raise NoReportError(_("The selected package does not contain any items."))
                filename = "full-material.zip"
                cfg = Config.getInstance()
                mimetype = cfg.getFileTypeMimeType( "ZIP" )
                self._req.content_type = """%s"""%(mimetype)
                self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
                self._req.sendfile(path)
            else:
                url = urlHandlers.UHConferenceDisplayMaterialPackage.getURL(self._conf)
                url.addParam("errors", _("You have to select at least one material type"))
                self._redirect( url )
        else:
            self._redirect( urlHandlers.UHConferenceDisplay.getURL( self._conf ) )


class RHShortURLRedirect(RH):

    def _checkParams( self, params ):
        self._tag = params.get("tag", "").strip()

    def _process(self):
        from MaKaC.conference import ConferenceHolder
        ch = ConferenceHolder()
        from MaKaC.common.url import ShortURLMapper
        sum = ShortURLMapper()
        if ch.hasKey(self._tag):
            conf = ch.getById(self._tag)
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(conf))
        elif sum.hasKey(self._tag):
            conf = sum.getById(self._tag)
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(conf))
        else:
            raise NoReportError(_("The specified event with id or tag \"%s\" does not exist or has been deleted")%self._tag)

