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

from pytz import timezone

from indico.core import signals
from indico.core.config import Config
from indico.modules.events.layout import layout_settings, theme_settings
from indico.modules.events.models.events import EventType
from indico.modules.events.operations import update_event
from indico.modules.events.util import track_time_changes
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.rooms import Room
from indico.util.i18n import _
from indico.web.flask.util import endpoint_for_url
import MaKaC.conference as conference
from MaKaC.common.url import ShortURLMapper
from MaKaC.common.utils import validMail, setValidEmailSeparators
from MaKaC.errors import FormValuesError


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
