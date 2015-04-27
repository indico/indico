# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.
from flask import session

from MaKaC.webinterface.rh import base
from MaKaC.common import xmlGen
from MaKaC.user import LoginInfo
from MaKaC.authentication import AuthenticatorMgr
from MaKaC.conference import CategoryManager


class RHXMLHandlerBase ( base.RH ):

    def _genStatus (self, statusValue, message, XG):
        XG.openTag("status")
        XG.writeTag("value", statusValue)
        XG.writeTag("message", message)
        XG.closeTag("status")

    def _createResponse (self, statusValue, message):
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        self._genStatus(statusValue, message, XG)
        XG.closeTag("response")

        self._responseUtil.content_type = 'text/xml'
        return XG.getXml()


class RHLoginStatus( RHXMLHandlerBase ):
    def _process( self ):
        XG = xmlGen.XMLGen()
        XG.openTag("response")
        self._genStatus("OK", "Request succesful", XG)
        XG.openTag("login-status")
        if session.avatar is not None:
            XG.writeTag("user-id", session.avatar.getId())
        XG.closeTag("login-status")
        XG.closeTag("response")

        self._responseUtil.content_type = 'text/xml'
        return XG.getXml()


class RHSignIn( RHXMLHandlerBase ):

    _isMobile = False

    def _checkParams( self, params ):

        self._login = params.get( "login", "" ).strip()
        self._password = params.get( "password", "" ).strip()

    def _process( self ):

        li = LoginInfo( self._login, self._password )
        av = AuthenticatorMgr().getAvatar(li)
        value = "OK"
        message = ""
        if not av:
            value = "ERROR"
            message = "Login failed"
        elif not av.isActivated():
            if av.isDisabled():
                value = "ERROR"
                message = "Acount is disabled"
            else:
                value = "ERROR"
                message = "Acount is not activated"
        else:
            value = "OK"
            message = "Login succesful"
            session.user = av.user

        return self._createResponse(value, message)


class RHSignOut( RHXMLHandlerBase ):

    def _process(self):
        if self._getUser():
            session.clear()
            self._setUser(None)

        return self._createResponse("OK", "Logged out")


class RHCategInfo( RHXMLHandlerBase ):

    def _checkParams( self, params ):
        self._id = params.get( "id", "" ).strip()
        self._fp = params.get( "fp", "no" ).strip()

    def _getHeader( self, XG ):
        XG.openTag("response")
        XG.openTag("status")
        XG.writeTag("value", "OK")
        XG.writeTag("message", "Returning category info")
        XG.closeTag("status")

    def _getFooter( self, XG ):
        XG.closeTag("response")

    def _getCategXML( self, cat, XG, fp="no" ):
        XG.openTag("categInfo")
        XG.writeTag("title",cat.getTitle())
        XG.writeTag("id",cat.getId())
        if fp == "yes":
            XG.openTag("father")
            if cat.getOwner():
                self._getCategXML(cat.getOwner(),XG,fp)
                fatherid = cat.getOwner().getId()
            XG.closeTag("father")
        XG.closeTag("categInfo")
        return XG.getXml()

    def _process( self ):
        self._responseUtil.content_type = 'text/xml'
        cm = CategoryManager()
        try:
            XG = xmlGen.XMLGen()
            cat = cm.getById(self._id)
            self._getHeader(XG)
            self._getCategXML(cat, XG, self._fp)
            self._getFooter(XG)
            return XG.getXml()
        except:
            value = "ERROR"
            message = "Category does not exist"
        if value != "OK":
            return self._createResponse(value, message)


class RHStatsIndico( RHXMLHandlerBase ):

    def _createIndicator( self, XG, name, fullname, value ):
        XG.openTag("indicator")
        XG.writeTag("name", name)
        XG.writeTag("fullname", fullname)
        XG.writeTag("value", value)
        XG.closeTag("indicator")

    def _process( self ):
        from datetime import datetime,timedelta
        from MaKaC.common.indexes import IndexesHolder

        self._responseUtil.content_type = 'text/xml'
        XG = xmlGen.XMLGen()
        XG.openTag("response")

        now = startdt = enddt = datetime.now()
        today = startdt.date()
        startdt.replace( hour = 0, minute = 0)
        enddt.replace( hour = 23, minute = 59)

        calIdx = IndexesHolder().getById("calendar")

        nbEvtsToday = len(calIdx.getObjectsInDay(now))
        nbOngoingEvts = len(calIdx.getObjectsIn(now,now))

        self._createIndicator(XG, "nbEventsToday", "total number of events for today", nbEvtsToday)
        self._createIndicator(XG, "nbOngoingEvents", "total number of ongoing events", nbOngoingEvts)
        XG.closeTag("response")
        return XG.getXml()
