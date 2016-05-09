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

from hashlib import md5
from operator import attrgetter

import lxml.etree
from lxml.etree import Element, SubElement
from pytz import timezone

from indico.modules.events.models.events import Event
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.util.string import to_unicode
from indico.web.flask.util import url_for


class XMLEventSerializer(object):
    def __init__(self, event, user=None, include_timetable=False, event_tag_name='event', include_announcer_email=None):
        self._user = user
        self._include_email = event.can_manage(user)
        self._event = event
        self._event_tag_name = event_tag_name
        self._include_timetable = include_timetable
        self._include_announcer_email = include_announcer_email

    def serialize_event(self):
        xml = self._serialize_event(self._event)
        return lxml.etree.tostring(xml, pretty_print=True)

    @staticmethod
    def _format_bool(boolean):
        return str(boolean).lower()

    def _format_date(self, date):
        return date.astimezone(self._tz).strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def _format_duration(duration):
        hours, seconds = divmod(int(duration.total_seconds()), 3600)
        minutes = seconds // 60
        return '{}:{:02}'.format(hours, minutes)

    @staticmethod
    def _color_tuple_to_attributes(color_tuple):
        return {
            'color': '#' + color_tuple.background,
            'textcolor': '#' + color_tuple.text
        }

    @staticmethod
    def _url_for(*args, **kwargs):
        kwargs['_external'] = True
        return url_for(*args, **kwargs)

    @staticmethod
    def _serialize_location(obj):
        """Serialize the location of an object extending LocationMixin"""
        xml = Element('location')
        SubElement(xml, 'name').text = obj.venue_name
        SubElement(xml, 'address').text = obj.address
        if obj.room_name:
            SubElement(xml, 'room').text = obj.room_name
            if obj.room:
                SubElement(xml, 'roomMapURL').text = obj.room.map_url
        return xml

    @staticmethod
    def _serialize_reference(reference):
        xml = Element('repno')
        SubElement(xml, 'system').text = reference.reference_type.name
        SubElement(xml, 'rn').text = reference.value
        return xml

    @staticmethod
    def _serialize_support_info(support_info):
        xml = Element('supportEmail', {
            'caption': to_unicode(support_info.getCaption())
        })
        xml.text = to_unicode(support_info.getEmail())
        return xml

    @staticmethod
    def _serialize_timezone(tzinfo):
        xml = Element('timezone')
        xml.text = tzinfo.zone
        return xml

    def _serialize_user(self, user, include_email=None):
        xml = Element('user')
        SubElement(xml, 'title').text = unicode(user.title)  # _LazyString not supported by lxml
        SubElement(xml, 'name', {
            'first': user.first_name,
            'last': user.last_name
        })
        SubElement(xml, 'organization').text = user.affiliation
        if include_email or (include_email is None and self._include_email):
            SubElement(xml, 'email').text = user.email
        SubElement(xml, 'emailHash').text = md5(user.email).hexdigest()
        SubElement(xml, 'userid').text = str(user.id)
        return xml

    def _serialize_event_person(self, tag_name, persons):
        xml = Element(tag_name)
        for person in persons:
            xml.append(self._serialize_user(person))
        return xml

    def _serialize_timetable_entry(self, entry):
        if entry.type == TimetableEntryType.SESSION_BLOCK:
            return self._serialize_session_block(entry.session_block)
        elif entry.type == TimetableEntryType.CONTRIBUTION:
            return self._serialize_contribution_block(entry)
        elif entry.type == TimetableEntryType.BREAK:
            return self._serialize_break(entry.break_)
        else:
            raise NotImplementedError()

    def _serialize_event(self, event):
        if self._user and self._user.settings.get('force_timezone'):
            self._tz = timezone(self._user.settings.get('timezone'))
        else:
            self._tz = event.tzinfo
        xml = Element(self._event_tag_name)
        SubElement(xml, '_deprecated').text = 'True'
        SubElement(xml, 'ID').text = str(event.id)
        SubElement(xml, 'category').text = event.category.name
        SubElement(xml, 'parentProtection').text = self._format_bool(event.is_protected)
        if event.can_manage(self._user):
            SubElement(xml, 'modifyLink').text = self._url_for('event_mgmt.conferenceModification', event)
            SubElement(xml, 'cloneLink').text = self._url_for('event_mgmt.confModifTools-clone', event)
        SubElement(xml, 'iCalLink').text = self._url_for('events.export_event_ical', event)
        SubElement(xml, 'announcer').append(self._serialize_user(event.creator,
                                                                 include_email=self._include_announcer_email))
        xml.append(self._serialize_support_info(event.as_legacy.getSupportInfo()))
        SubElement(xml, 'title').text = event.title
        SubElement(xml, 'description').text = event.description
        SubElement(xml, 'closed').text = str(event.as_legacy.isClosed())
        xml.append(self._serialize_location(event))
        SubElement(xml, 'startDate').text = self._format_date(event.start_dt)
        SubElement(xml, 'endDate').text = self._format_date(event.end_dt)
        SubElement(xml, 'creationDate').text = self._format_date(event.as_legacy.getCreationDate())
        SubElement(xml, 'modificationDate').text = self._format_date(event.as_legacy.getModificationDate())
        xml.append(self._serialize_timezone(self._tz))
        if self._include_timetable:
            for entry in event.timetable_entries.filter(TimetableEntry.parent == None):
                xml.append(self._serialize_timetable_entry(entry))
        return xml

    def _serialize_session_block(self, session_block):
        session = session_block.session
        slot_id = sorted(session_block.session.blocks, key=attrgetter('start_dt')).index(session_block)
        xml = Element('session', self._color_tuple_to_attributes(session.colors))
        SubElement(xml, 'ID').text = str(session.friendly_id)
        SubElement(xml, 'new_id').text = str(session.id)
        SubElement(xml, 'parentProtection').text = self._format_bool(session.is_protected)
        SubElement(xml, 'code').text = 'sess{}-{}'.format(session.friendly_id, slot_id + 1)
        SubElement(xml, 'slotId').text = str(slot_id)
        SubElement(xml, 'sessionTimetableLink').text = self._url_for('sessions.display_session',
                                                                     session)
        title = session.title
        if session_block.title:
            title += ': ' + session_block.title
        SubElement(xml, 'title').text = title
        if session_block.can_manage(self._user):
            SubElement(xml, 'modifyLink').text = self._url_for('timetable.manage_session', session)
        SubElement(xml, 'description').text = session.description.replace('\r\n', '\n')
        xml.append(self._serialize_location(session_block))
        SubElement(xml, 'startDate').text = self._format_date(session_block.start_dt)
        SubElement(xml, 'endDate').text = self._format_date(session_block.end_dt)
        SubElement(xml, 'duration').text = self._format_duration(session_block.duration)
        for entry in session_block.timetable_entry.children:
            xml.append(self._serialize_timetable_entry(entry))
        return xml

    def _serialize_contribution_block(self, contribution_block):
        contribution = contribution_block.contribution
        xml = Element('contribution')
        SubElement(xml, 'ID').text = str(contribution.friendly_id)
        SubElement(xml, 'new_id').text = str(contribution.id)
        SubElement(xml, 'parentProtection').text = self._format_bool(contribution.is_protected)
        if contribution.board_number:
            SubElement(xml, 'board').text = contribution.board_number
        if contribution.track:
            SubElement(xml, 'track').text = contribution.track.getTitle()
        if contribution.type:
            type_xml = SubElement(xml, 'type')
            SubElement(type_xml, 'ID').text = str(contribution.type.id)
            SubElement(type_xml, 'name').text = contribution_block.contribution.type.name
        if contribution.can_manage(self._user):
            SubElement(xml, 'modifyLink').text = self._url_for('contributions.manage_contributions',
                                                               contribution.event_new)
        if contribution.keywords:
            keywords_xml = SubElement(xml, 'keywords')
            for keyword in contribution.keywords:
                SubElement(keywords_xml, 'keyword').text = keyword
        for reference in contribution.references:
            xml.append(self._serialize_reference(reference))
        SubElement(xml, 'title').text = contribution.title
        if contribution.speakers:
            xml.append(self._serialize_event_person('speakers', contribution.speakers))
        if contribution.primary_authors:
            xml.append(self._serialize_event_person('primaryAuthors', contribution.primary_authors))
        if contribution.secondary_authors:
            xml.append(self._serialize_event_person('coAuthors', contribution.secondary_authors))
        xml.append(self._serialize_location(contribution))
        SubElement(xml, 'startDate').text = self._format_date(contribution_block.start_dt)
        SubElement(xml, 'endDate').text = self._format_date(contribution_block.end_dt)
        SubElement(xml, 'duration').text = self._format_duration(contribution_block.duration)
        # Text is not properly escaped when passing a MarkdownText instance
        SubElement(xml, 'abstract').text = unicode(contribution.description).replace('\r\n', '\n')
        for subcontrib in contribution.subcontributions:
            xml.append(self._serialize_subcontribution(subcontrib))
        return xml

    def _serialize_subcontribution(self, subcontrib):
        xml = Element('subcontribution')
        SubElement(xml, 'ID').text = str(subcontrib.friendly_id)
        SubElement(xml, 'new_id').text = str(subcontrib.id)
        SubElement(xml, 'parentProtection').text = self._format_bool(subcontrib.is_protected)
        if subcontrib.can_manage(self._user):
            SubElement(xml, 'modifyLink').text = self._url_for('contributions.manage_contributions',
                                                               subcontrib.event_new)
        for reference in subcontrib.references:
            xml.append(self._serialize_reference(reference))
        SubElement(xml, 'title').text = subcontrib.title
        if subcontrib.speakers:
            xml.append(self._serialize_event_person('speakers', subcontrib.speakers))
        # Text is not properly escaped when passing a MarkdownText instance
        SubElement(xml, 'duration').text = self._format_duration(subcontrib.duration)
        SubElement(xml, 'abstract').text = unicode(subcontrib.description).replace('\r\n', '\n')
        return xml

    def _serialize_break(self, break_):
        xml = Element('break', {
            'color': break_.colors.background,
            'textcolor': break_.colors.text
        })
        SubElement(xml, 'name').text = break_.title
        SubElement(xml, 'startDate').text = self._format_date(break_.start_dt)
        SubElement(xml, 'endDate').text = self._format_date(break_.end_dt)
        SubElement(xml, 'duration').text = self._format_duration(break_.duration)
        xml.append(self._serialize_location(break_))
        return xml
