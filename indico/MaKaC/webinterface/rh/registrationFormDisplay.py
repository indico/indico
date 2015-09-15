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
from flask import session, flash, redirect
from cStringIO import StringIO

from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.registrationForm as registrationForm
from MaKaC import registration
from MaKaC.errors import FormValuesError, MaKaCError, AccessError, NotFoundError
from MaKaC.webinterface.rh.registrantsModif import RHRegistrantListModif

from MaKaC.common.utils import validMail
from MaKaC.PDFinterface.conference import TicketToPDF
from indico.modules.auth.util import redirect_to_login
from indico.modules.events.logs import EventLogRealm, EventLogKind
from indico.modules.events.registration.notifications import (notify_registration_confirmation,
                                                              notify_registration_modification)
from indico.modules.payment import event_settings as payment_event_settings
from indico.modules.users.util import get_user_by_email
from indico.web.flask.util import send_file, url_for

from indico.util import json
from indico.util.i18n import set_best_lang, _
from indico.util.string import to_unicode


class RHBaseRegistrationForm(RHConferenceBaseDisplay):

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()

    def _processIfActive(self):
        """only override this method if the RegForm must be activated for
            carrying on the handler execution"""
        return "regForm"

    def _process(self):
        #if the RegForm is not activated we show up a form informing about that.
        #   This must be done at RH level because there can be some RH not
        #   displaying pages.
        if not self._regForm.isActivated() or not self._conf.hasEnabledSection("regForm"):
            p = registrationForm.WPRegFormInactive(self, self._conf)
            return p.display()
        else:
            return self._processIfActive()


class RHRegistrationFormDisplayBase(RHBaseRegistrationForm):
    _uh = urlHandlers.UHConfRegistrationFormDisplay


class RHRegistrationFormDisplayBaseCheckProtection(RHRegistrationFormDisplayBase):
    def _checkProtection(self):
        RHRegistrationFormDisplayBase._checkProtection(self)
        if self._regForm.inRegistrationPeriod() and self._regForm.isMandatoryAccount() and self._getUser() is None:
            self._redirect(redirect_to_login(reason=_("You are trying to register for an event that requires you to be "
                                                      "logged in.")))
            self._doProcess = False


class RHRegistrationFormDisplay(RHRegistrationFormDisplayBaseCheckProtection):
    _uh = urlHandlers.UHConfRegistrationFormDisplay

    def _processIfActive(self):
        if (self._conf.getRegistrationForm().isFull() or
                not self._conf.getRegistrationForm().inRegistrationPeriod() or
                (session.avatar and session.avatar.isRegisteredInConf(self._conf))):
            return redirect(url_for('event.confRegistrationFormDisplay', self._conf))
        return registrationForm.WPRegistrationFormDisplay(self, self._conf).display()


class RHRegistrationFormCreation(RHRegistrationFormDisplayBaseCheckProtection):
    _uh = urlHandlers.UHConfRegistrationFormDisplay

    def __init__(self, is_manager=False):
        RHRegistrationFormDisplayBaseCheckProtection.__init__(self)
        self.is_manager = is_manager

    def _checkParams(self, params):
        RHBaseRegistrationForm._checkParams(self, params)
        self._regForm = self._conf.getRegistrationForm()
        # SESSIONS
        sessionForm = self._regForm.getSessionsForm()
        sessions = sessionForm.getSessionsFromParams(params)
        params["sessions"] = sessions
        # ACCOMMODATION
        params["accommodationType"] = self._regForm.getAccommodationForm().getAccommodationTypeById(params.get("accommodation_type", ""))
        # SOCIAL EVENTS
        socialEventIds = self._normaliseListParam(params.get("socialEvents", []))
        se = []
        for id in socialEventIds:
            se.append(self._regForm.getSocialEventForm().getSocialEventById(id))
        params["socialEvents"] = se

    def _process(self):
        canManageRegistration = self._conf.canManageRegistration(self._getUser())
        if not canManageRegistration and not self._regForm.isActivated():
            p = registrationForm.WPRegFormInactive(self, self._conf)
            return p.display()
        params = self._getRequestParams()
        email = self._regForm.getPersonalData().getValueFromParams(params, 'email')
        if email is None:
            raise FormValuesError(_("An email address has to be set in order to make the registration in the event."))
        elif not validMail(email, False):
            raise FormValuesError(_("The given email address is not valid."))

        # Check if the email matches an existing user
        user = get_user_by_email(email)
        avatar = user.as_avatar if user else None

        # Check if the user can register
        if not canManageRegistration:  # normal user registering. Managers can.
            if self._conf.getRegistrationForm().isFull():
                self._redirect(urlHandlers.UHConfRegistrationFormDisplay.getURL(self._conf))
                return
            elif not self._conf.getRegistrationForm().inRegistrationPeriod():
                flash(_("Your registration couldn't be recorded."), 'error')
                return redirect(url_for('event.confRegistrationFormDisplay', self._conf))
        if user is None:
            if self._conf.hasRegistrantByEmail(email):
                raise FormValuesError("There is already a user with the email \"%s\". Please choose another one" % email)
        else:
            if avatar.isRegisteredInConf(self._conf) or self._conf.hasRegistrantByEmail(email):
                if canManageRegistration:
                    raise FormValuesError("There is already a user with the email \"%s\". Please choose another one" % email)
                else:
                    raise FormValuesError("You have already registered with the email address \"%s\". If you need to modify your registration, please contact the managers of the conference." % email)

        rp = registration.Registrant()
        self._conf.addRegistrant(rp, avatar)
        rp.setValues(self._getRequestParams(), avatar)

        if avatar is not None:
            rp.setAvatar(avatar)

        notify_registration_confirmation(self._conf, rp)
        self._conf.log(EventLogRealm.management if self.is_manager else EventLogRealm.participants,
                       EventLogKind.positive, u'Registration',
                       u'User registered: {}'.format(to_unicode(rp.getFullName(title=False, firstNameFirst=True))),
                       session.user,
                       data={u'Indico user': u'{} ({})'.format(user.full_name, user.id) if user else u'None'})

        if self.is_manager:
            self._redirect(RHRegistrantListModif._uh.getURL(self._conf))
        else:
            params = {}
            if not rp.doPay() or not payment_event_settings.get(self._conf, 'enabled'):
                flash(_(u"Your registration has been recorded successfully."), 'success')
            if not session.user or session.user != user:
                params.update(rp.getLocator(), **{'authkey': rp.getRandomId()})
            else:
                params.update(self._conf.getLocator())
            return redirect(url_for('event.confRegistrationFormDisplay', **params))


class RHRegistrationForm(RHRegistrationFormDisplayBase):
    _uh = urlHandlers.UHConfRegistrationForm

    def _checkParams(self, params):
        RHRegistrationFormDisplayBase._checkParams(self, params)
        self._registrant = None
        self._registrant_id = params.get('registrantId', None)
        self._authkey = None
        if self._registrant_id:
            self._registrant = self._conf.getRegistrantById(self._registrant_id)
            if self._registrant is None:
                raise NotFoundError(_("The registrant with id {} does not exist or has been deleted")
                                    .format(self._registrant_id))
            self._authkey = params.get('authkey', '')
            if self._registrant.getRandomId() != self._authkey or self._authkey == '':
                raise AccessError()
        elif session.avatar:
            self._registrant = session.avatar.getRegistrantById(self._conf.getId())

    def _processIfActive(self):
        p = registrationForm.WPRegistrationForm(self, self._conf)
        return p.display(registrant=self._registrant, registrant_id=self._registrant_id, authkey=self._authkey)


class RHRegistrationFormRegistrantBase(RHRegistrationForm):
    def _checkParams(self, params):
        RHRegistrationForm._checkParams(self, params)
        if self._registrant is None:
            if not session.user and not params.get('registrantId', None):
                raise MaKaCError(_("registrant id not set"))
            raise NotFoundError(_("You are not registered or your registration has been deleted"))


class RHConferenceTicketPDF(RHRegistrationFormRegistrantBase):
    def _checkProtection(self):
        RHRegistrationFormRegistrantBase._checkProtection(self)
        if self._regForm.inRegistrationPeriod() and self._regForm.isMandatoryAccount() and self._getUser() is None:
            self._redirect(self._getLoginURL())
            self._doProcess = False

    def _process(self):
        set_best_lang()  # prevents from having a _LazyString when generating a pdf without session.lang set
        filename = "{0}-Ticket.pdf".format(self._target.getTitle())
        pdf = TicketToPDF(self._target, self._registrant)
        return send_file(filename, StringIO(pdf.getPDFBin()), 'PDF')


class RHRegistrationFormModify(RHRegistrationFormDisplayBaseCheckProtection):
    _uh = urlHandlers.UHConfRegistrationFormDisplay

    def _checkParams(self, params):
        RHRegistrationFormDisplayBase._checkParams(self, params)
        self._registrant = session.avatar.getRegistrantById(self._conf.getId()) if session.avatar else None

    def _processIfActive(self):
        if not self._registrant:
            return redirect(url_for('event.confRegistrationFormDisplay-display', self._conf))
        if not self._regForm.inModificationPeriod():
            flash(_("The modification period is over."), 'error')
            return redirect(url_for('event.confRegistrationFormDisplay', self._conf))
        return registrationForm.WPRegistrationFormModify(self, self._conf).display()


class RHRegistrationFormPerformModify(RHRegistrationFormCreation):
    _uh = urlHandlers.UHConfRegistrationFormModify

    def _process(self):
        if self._getUser() is not None and self._getUser().isRegisteredInConf(self._conf):
            if not self._conf.getRegistrationForm().inRegistrationPeriod() and not self._conf.getRegistrationForm().inModificationPeriod():
                flash(_("Your modification could not be recorded since the modification period is over."), 'error')
                return redirect(url_for('event.confRegistrationFormDisplay', self._conf))
            else:
                rp = self._getUser().getRegistrantById(self._conf.getId())

                # Check if the email matches an existing user
                params = self._getRequestParams()
                email = self._regForm.getPersonalData().getValueFromParams(params, 'email') or ''
                user = get_user_by_email(email)
                if user:
                    if not session.user:
                        flash(_('The provided email ({email}) is linked to an Indico account. Please sign in with it '
                                'first.').format(email=email), 'error')
                        return redirect(url_for('event.confRegistrationFormDisplay-modify', self._conf))
                    elif session.user != user:
                        flash(_('The provided email ({email}) is linked to another Indico account. Please sign in with '
                                'it first.').format(email=email), 'error')
                        return redirect(url_for('event.confRegistrationFormDisplay-modify', self._conf))

                # check if the email is being changed by another one that already exists
                if email != rp.getEmail() and self._conf.hasRegistrantByEmail(email):
                    raise FormValuesError(_("There is already a user with the email \"{email}\". "
                                            "Please choose another one.").format(email or "--no email--"))
                rp.setValues(self._getRequestParams(), self._getUser())
                log_msg = u'User modified his registration data: {}'
                self._conf.log(EventLogRealm.participants, EventLogKind.positive, u'Registration',
                               log_msg.format(to_unicode(rp.getFullName(title=False, firstNameFirst=True))),
                               session.user,
                               data={u'Indico user': u'{} ({})'.format(user.full_name, user.id) if user else u'None'})
                notify_registration_modification(self._conf, rp)
                flash(_(u"Your registration has been modified successfully."), 'success')
                if rp.doPay():
                    self._redirect(urlHandlers.UHConfRegistrationFormCreationDone.getURL(rp))
                else:
                    self._redirect(urlHandlers.UHConfRegistrationForm.getURL(self._conf))
        else:
            self._redirect(urlHandlers.UHConfRegistrationForm.getURL(self._conf))


class RHRegistrationFormConditions(RHRegistrationFormDisplayBaseCheckProtection):

    def _process(self):
        p = registrationForm.WPRegistrationFormConditions(self, self._conf)
        return p.display()


class RHRegistrationFormUserData(RHRegistrationFormDisplayBaseCheckProtection):

    def _checkProtection(self):
        RHBaseRegistrationForm._checkProtection(self)

    def _process(self):
        user = self._aw.getUser()
        reg_data = {}
        if user is not None:
            if user.isRegisteredInConf(self._conf):
                registrant = user.getRegistrantById(self._conf.getId())
                reg_data = registrant.fossilize()
            else:
                personalData = self._regForm.getPersonalData()
                reg_data['avatar'] = personalData.getFormValuesFromAvatar(user)
                reg_data['avatar'].setdefault('sessionList', [{}, {}])
        else:
            reg_data['avatar'] = {'sessionList': [{}, {}]}
        return json.dumps(reg_data)
