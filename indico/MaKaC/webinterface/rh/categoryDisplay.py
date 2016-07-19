# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import json
import re
from datetime import timedelta, datetime

from flask import session
from pytz import timezone

from MaKaC.common.url import ShortURLMapper
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.category as category
from MaKaC.errors import MaKaCError, FormValuesError
import MaKaC.conference as conference
from indico.core import signals
from indico.core.config import Config
from MaKaC.i18n import _
from MaKaC.webinterface.user import UserListModificationBase
from MaKaC.common.utils import validMail, setValidEmailSeparators

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.categories.controllers.base import RHCreateEventBase
from indico.modules.events.forms import EventPersonLinkForm
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.notifications import notify_event_creation
from indico.modules.events.operations import update_event
from indico.modules.events.util import track_time_changes
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.locations import Location
from indico.util.string import to_unicode
from indico.web.flask.util import endpoint_for_url


class RHConferenceCreation(RHCreateEventBase):
    def _checkParams(self, params):
        self._params = params
        RHCreateEventBase._checkParams(self)

    def _process(self):
        if not self._event_type:
            raise MaKaCError("No event type specified")
        else:
            p = category.WPConferenceCreationMainData(self, self.category)
            if self._wf is not None:
                p = self._wf.getEventCreationPage(self, self.category)
            return p.display(**self._params)


class RHConferencePerformCreation(RHCreateEventBase):
    def _checkParams(self, params):
        self._params = params
        RHCreateEventBase._checkParams(self)
        self._datecheck = False
        self._confirm = False
        self._performedAction = ""
        if "ok" in params:
            self._confirm = True

    def _process( self ):
        params = self._getRequestParams()
        if params["title"]=="":
            params["title"]="No Title"
        # change number of dates (lecture)
        if self._confirm == True:
            if self._event_type != EventType.lecture:
                c = self._createEvent( self._params )
                self.alertCreation([c], to_unicode(params['title']))
            # lectures
            else:
                lectures = []
                for i in range (1, int(self._params["nbDates"])+1):
                    self._params["sDay"] = self._params.get("sDay_%s"%i,"")
                    self._params["sMonth"] = self._params.get("sMonth_%s"%i,"")
                    self._params["sYear"] = self._params.get("sYear_%s"%i,"")
                    self._params["sHour"] = self._params.get("sHour_%s"%i,"")
                    self._params["sMinute"] = self._params.get("sMinute_%s"%i,"")
                    self._params["duration"] = int(self._params.get("dur_%s"%i,60))
                    lectures.append(self._createEvent(self._params))
                self.alertCreation(lectures, to_unicode(params['title']))
                lectures.sort(sortByStartDate)
                # create links
                for i, source in enumerate(lectures, 1):
                    if len(lectures) > 1:
                        source.setTitle("{} ({}/{})".format(source.getTitle(), i, len(lectures)))

                    for j, target in enumerate(lectures, 1):
                        if j != i:
                            folder = AttachmentFolder(object=source.as_event, title="part{}".format(j))
                            link = Attachment(user=session.user, type=AttachmentType.link,
                                              folder=folder, title="Part {}".format(j),
                                              link_url=target.getURL())
                            db.session.add(link)
                c = lectures[0]
            self._redirect(urlHandlers.UHConferenceModification.getURL( c ) )
        else :
            self._redirect(self.category.url)

    def _createEvent(self, params):
        kwargs = UtilsConference.get_new_conference_kwargs(self._params)
        if kwargs['start_dt'] >= kwargs['end_dt']:
            raise FormValuesError(_('The start date cannot be after the end date.'))
        c = conference.Conference.new(self.category, creator=session.user, event_type=self._event_type, **kwargs)
        UtilsConference.setValues(c, self._params)

        eventAccessProtection = params.get("eventProtection", "inherit")
        if eventAccessProtection == "private" :
            c.as_event.protection_mode = ProtectionMode.protected
        elif eventAccessProtection == "public" :
            c.as_event.protection_mode = ProtectionMode.public

        for legacy_principal in self._getPersons():
            c.as_event.update_principal(legacy_principal.as_new, read_access=True)

        # Add EventPersonLinks to the Event
        person_links = self.get_event_person_links_data(c.as_event)
        update_event(c.as_event, {'person_link_data': person_links})

        return c

    def get_event_person_links_data(self, event):
        form = EventPersonLinkForm(event=event, event_type=event.type)
        if not form.validate_on_submit():
            raise FormValuesError(form.errors)
        return form.person_link_data.data

    def _getPersons(self):
        from MaKaC.services.interface.rpc import json
        allowedUsersDict = json.decode(self._params.get("allowedUsers") or "[]") or []
        return UserListModificationBase.retrieveUsers({"userList": allowedUsersDict})[0] if allowedUsersDict else []

    def alertCreation(self, confs, title):
        occurrences = [conf.as_event for conf in confs] if len(confs) > 1 else None
        notify_event_creation(confs[0].as_event, title, occurrences)


class UtilsConference:
    @staticmethod
    def get_start_dt(params):
        tz = params['Timezone']
        try:
            return timezone(tz).localize(datetime(int(params['sYear']), int(params['sMonth']), int(params['sDay']),
                                                  int(params['sHour']), int(params['sMinute'])))
        except ValueError as e:
            raise FormValuesError('The start date you have entered is not correct: {}'.format(e), 'Event')

    @staticmethod
    def get_end_dt(params, start_dt):
        tz = params['Timezone']
        if params.get('duration'):
            end_dt = start_dt + timedelta(minutes=params['duration'])
        else:
            try:
                end_dt = timezone(tz).localize(datetime(int(params['eYear']), int(params['eMonth']),
                                                        int(params['eDay']), int(params['eHour']),
                                                        int(params['eMinute'])))
            except ValueError as e:
                raise FormValuesError('The end date you have entered is not correct: {}'.format(e), 'Event')
        return end_dt

    @staticmethod
    def get_location_data(params):
        location_data = json.loads(params['location_data'])
        if location_data.get('room_id'):
            location_data['room'] = Room.get_one(location_data['room_id'])
        if location_data.get('venue_id'):
            location_data['venue'] = Location.get_one(location_data['venue_id'])
        return location_data

    @classmethod
    def get_new_conference_kwargs(cls, params):
        start_dt = cls.get_start_dt(params)
        end_dt = cls.get_end_dt(params, start_dt)
        return {'title': params['title'],
                'timezone': unicode(params['Timezone']),
                'start_dt': start_dt,
                'end_dt': end_dt}

    @classmethod
    def setValues(cls, c, confData, notify=False):
        c.setTitle( confData["title"] )
        c.setDescription( confData["description"] )
        c.setOrgText(confData.get("orgText",""))
        c.setComments(confData.get("comments",""))
        c.setKeywords( confData["keywords"] )
        c.setChairmanText( confData.get("chairText", "") )
        if "shortURLTag" in confData.keys():
            tag = confData["shortURLTag"].strip()
            if tag:
                try:
                    UtilsConference.validateShortURL(tag, c)
                except ValueError, e:
                    raise FormValuesError(e.message)
            if c.getUrlTag() != tag:
                mapper = ShortURLMapper()
                mapper.remove(c)
                c.setUrlTag(tag)
                if tag:
                    mapper.add(tag, c)
        c.setContactInfo( confData.get("contactInfo","") )
        #################################
        # Fermi timezone awareness      #
        #################################
        c.setTimezone(confData["Timezone"])
        sDate = cls.get_start_dt(confData)
        eDate = cls.get_end_dt(confData, sDate)
        moveEntries = int(confData.get("move",0))
        with track_time_changes():
            c.setDates(sDate.astimezone(timezone('UTC')), eDate.astimezone(timezone('UTC')), moveEntries=moveEntries)

        #################################
        # Fermi timezone awareness(end) #
        #################################

        old_location_data = c.as_event.location_data
        location_data = cls.get_location_data(confData)
        update_event(c.as_event, {'location_data': location_data})

        if old_location_data != location_data:
            signals.event.data_changed.send(c, attr='location', old=old_location_data, new=location_data)

        emailstr = setValidEmailSeparators(confData.get("supportEmail", ""))

        if (emailstr != "") and not validMail(emailstr):
            raise FormValuesError("One of the emails specified or one of the separators is invalid")

        c.getSupportInfo().setEmail(emailstr)
        c.getSupportInfo().setCaption(confData.get("supportCaption","Support"))
        # TODO: remove TODO once visibility has been updated
        if c.getVisibility() != confData.get("visibility", 999) and confData.get('visibility') != 'TODO':
            c.setVisibility(confData.get("visibility", 999))
        theme = confData.get('defaultStyle', '')
        new_type = EventType.legacy_map[confData['eventType']] if 'eventType' in confData else c.as_event.type_
        if new_type != c.as_event.type_:
            c.as_event.type_ = new_type
        elif not theme or theme == theme_settings.defaults.get(new_type.legacy_name):
            # if it's the default theme or nothing was set (does this ever happen?!), we don't store it
            layout_settings.delete(c, 'timetable_theme')
        else:
            # set the new theme
            layout_settings.set(c, 'timetable_theme', theme)

    @staticmethod
    def validateShortURL(tag, target):
        if tag.isdigit():
            raise ValueError(_("Short URL tag is a number: '%s'. Please add at least one non-digit.") % tag)
        if not re.match(r'^[a-zA-Z0-9/._-]+$', tag) or '//' in tag:
            raise ValueError(
                _("Short URL tag contains invalid chars: '%s'. Please select another one.") % tag)
        if tag[0] == '/' or tag[-1] == '/':
            raise ValueError(
                _("Short URL tag may not begin/end with a slash: '%s'. Please select another one.") % tag)
        mapper = ShortURLMapper()
        if mapper.hasKey(tag) and mapper.getById(tag) != target:
            raise ValueError(_("Short URL tag already used: '%s'. Please select another one.") % tag)
        if conference.ConferenceHolder().hasKey(tag):
            # Reject existing event ids. It'd be EXTREMELY confusing and broken to allow such a shorturl
            raise ValueError(_("Short URL tag is an event id: '%s'. Please select another one.") % tag)
        ep = endpoint_for_url(Config.getInstance().getShortEventURL() + tag)
        if not ep or ep[0] != 'event.shorturl':
            # URL does not match the shorturl rule or collides with an existing rule that does does not
            # know about shorturls.
            # This shouldn't happen anymore with the /e/ namespace but we keep the check just to be safe
            raise ValueError(
                _("Short URL tag conflicts with an URL used by Indico: '%s'. Please select another one.") % tag)


def sortByStartDate(conf1,conf2):
    return cmp(conf1.getStartDate(),conf2.getStartDate())
