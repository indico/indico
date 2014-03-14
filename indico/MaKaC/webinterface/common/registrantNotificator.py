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

"""
"""

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.review as review
from MaKaC.common import log
from MaKaC.webinterface.mail import GenericMailer
from MaKaC.webinterface.common.baseNotificator import TplVar, Notification


class ConfTitleTplVar(TplVar):
    _name="conference_title"
    _description=""

    def getValue(cls,registrant):
        return registrant.getConference().getTitle()
    getValue=classmethod(getValue)


class ConfURLTplVar(TplVar):
    _name="conference_URL"
    _description=""

    def getValue(cls,registrant):
        return str(urlHandlers.UHConferenceDisplay.getURL(registrant.getConference()))
    getValue=classmethod(getValue)

class RegistrantIdTplVar(TplVar):
    _name="registrant_id"
    _description=""

    def getValue(cls,registrant):
        return registrant.getId()
    getValue=classmethod(getValue)


class RegistrantFirstNameTplVar(TplVar):
    _name="registrant_first_name"
    _description=""

    def getValue(cls,registrant):
        return registrant.getFirstName()
    getValue=classmethod(getValue)

class RegistrantFamilyNameTplVar(TplVar):
    _name="registrant_family_name"
    _description=""

    def getValue(cls,registrant):
        return registrant.getFamilyName()
    getValue=classmethod(getValue)

class RegistrantTitleTplVar(TplVar):
    _name="registrant_title"
    _description=""

    def getValue(cls,registrant):
        return registrant.getTitle()
    getValue=classmethod(getValue)

class RegistrantAccommodationTplVar(TplVar):
    _name="registrant_accommodation"
    _description=""

    def getValue(cls,registrant):
        if registrant.getAccommodation() is not None and \
                registrant.getAccommodation().getAccommodationType() is not None:
                    return registrant.getAccommodation().getAccommodationType().getCaption()
        return ""
    getValue=classmethod(getValue)

class RegistrantSocialEventsTplVar(TplVar):
    _name="registrant_social_events"
    _description=""

    def getValue(cls,registrant):
        selist=[]
        for se in registrant.getSocialEvents():
            selist.append("%s [%s place(s)]"%(se.getCaption(), se.getNoPlaces()))
        return ", ".join(selist)
    getValue=classmethod(getValue)

class RegistrantSessionsTplVar(TplVar):
    _name="registrant_sessions"
    _description=""

    def getValue(cls,registrant):
        selist=[]
        for se in registrant.getSessionList():
            selist.append(se.getTitle())
        return ", ".join(selist)
    getValue=classmethod(getValue)

class RegistrantArrivalDateTplVar(TplVar):
    _name="registrant_arrival_date"
    _description=""

    def getValue(cls,registrant):
        arrivalDate=""
        if registrant.getAccommodation() is not None and registrant.getAccommodation().getArrivalDate() is not None:
            arrivalDate = registrant.getAccommodation().getArrivalDate().strftime("%d-%B-%Y")
        return arrivalDate
    getValue=classmethod(getValue)

class RegistrantDepartureDateTplVar(TplVar):
    _name="registrant_departure_date"
    _description=""

    @classmethod
    def getValue(cls,registrant):
        departureDate=""
        if registrant.getAccommodation() is not None and registrant.getAccommodation().getDepartureDate() is not None:
            departureDate = registrant.getAccommodation().getDepartureDate().strftime("%d-%B-%Y")
        return departureDate


class RegistrantPaymentLinkTplVar(TplVar):
    _name="registrant_payment_link"
    _description=""

    @classmethod
    def getValue(cls,registrant):
        return urlHandlers.UHConfRegistrationFormCreationDone.getURL(registrant)


class Notificator:
    _vars = [ConfTitleTplVar, ConfURLTplVar, RegistrantIdTplVar, RegistrantFirstNameTplVar, RegistrantFamilyNameTplVar,
             RegistrantTitleTplVar, RegistrantAccommodationTplVar, RegistrantSocialEventsTplVar,
             RegistrantSessionsTplVar, RegistrantArrivalDateTplVar, RegistrantDepartureDateTplVar,
             RegistrantPaymentLinkTplVar]

    @classmethod
    def getVarList(cls):
        return cls._vars

    def _getVars(self, registrant):
        d = {}
        for v in self.getVarList():
            d[v.getName()] = v.getValue(registrant)
        return d


class EmailNotificator(Notificator):

    def apply(self,registrant,params):
        v=self._getVars(registrant)
        subj=params.get("subject","").format(**v)
        b=params.get("body","").format(**v)
        fa=params.get("from","")
        tl=params.get("to",[])
        cc = params.get("cc",[])
        return Notification(subject=subj,body=b,fromAddr=fa,toList=tl,ccList=cc)

    def notify(self,registrant,params):
        if params.has_key("conf"):
            GenericMailer.sendAndLog(self.apply(registrant,params),
                                     params["conf"],
                                     log.ModuleNames.REGISTRATION)
        else:
            GenericMailer.send(self.apply(registrant,params))

    def notifyAll(self,params):
        subj=params.get("subject","")
        b=params.get("body","")
        fa=params.get("from","")
        tl=params.get("to",[])
        cc = params.get("cc",[])
        notification =  Notification(subject=subj,body=b,fromAddr=fa,toList=tl,ccList=cc)
        if params.has_key("conf"):
            GenericMailer.sendAndLog(notification, params["conf"],
                                     log.ModuleNames.REGISTRATION)
        else:
            GenericMailer.send(notification)
