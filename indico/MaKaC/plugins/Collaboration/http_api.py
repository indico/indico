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

import icalendar as ical
from datetime import timedelta

from indico.core.index import Catalog
from indico.web.http_api.hooks.base import HTTPAPIHook, IteratedDataFetcher
from indico.web.http_api.metadata.ical import ICalSerializer
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError

from MaKaC.plugins.Collaboration.handlers import RCCollaborationAdmin
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.conference import ConferenceHolder
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.plugins.Collaboration.fossils import ICollaborationMetadataFossil
from MaKaC.common.timezoneUtils import getAdjustedDate


globalHTTPAPIHooks = ['CollaborationAPIHook', 'CollaborationExportHook', 'VideoEventHook']


def serialize_collaboration_alarm(fossil, now):
    alarm = ical.Alarm()
    trigger = timedelta(minutes=-int(fossil['alarm']))
    alarm.set('trigger', trigger)
    alarm.set('action', 'DISPLAY')
    alarm.set('summary', VideoExportUtilities.getCondensedPrefix(fossil['type'],
                                                                 fossil['status']) + fossil['title'].decode('utf-8'))
    alarm.set('description', str(fossil['url']))

    return alarm


def serialize_collaboration(cal, fossil, now):
    event = ical.Event()
    url = str(fossil['url'])
    event.set('uid', 'indico-collaboration-%s@cern.ch' % fossil['uniqueId'])
    event.set('dtstamp', now)
    event.set('dtstart', getAdjustedDate(fossil['startDate'], None, "UTC"))
    event.set('dtend', getAdjustedDate(fossil['endDate'], None, "UTC"))
    event.set('url', url)
    event.set('categories', "VideoService - " + fossil['type'])
    event.set('summary', VideoExportUtilities.getCondensedPrefix(fossil['type'],
                                                                 fossil['status']) + fossil['title'].decode('utf-8'))
    loc = fossil.get('location', '')
    if loc:
        loc = loc.decode('utf-8')
    if fossil.get('room',''):
        loc += ': ' + fossil['room'].decode('utf-8')
    event.set('location', loc)
    description = "Event URL: " + url
    audience = fossil.get("audience", None)
    if audience:
        description = "Audience: %s\n"% audience + description
    event.set('description', description)

    # If there is an alarm required, add a subcomponent to the Event
    if fossil.has_key('alarm'):
        event.add_component(serialize_collaboration_alarm(fossil, now))
    cal.add_component(event)


# the iCal serializer needs some extra info on how to display things
ICalSerializer.register_mapper('collaborationMetadata', serialize_collaboration)


class VideoExportUtilities():

    SERVICE_MAP = {
        'CERNMCU': 'MCU',
        'WebcastRequest': 'W',
        'RecordingRequest': 'R'
    }

    @staticmethod
    def getCondensedPrefix(service, status):
        """ Condense down the summary lines based on the above dictionaries
            for easier reading in calendar applications.
        """
        prefix = ""

        if VideoExportUtilities.SERVICE_MAP.has_key(service):
            prefix += VideoExportUtilities.SERVICE_MAP.get(service)
        else:
            prefix += service

        if status:
            prefix += '-' + status

        return (prefix + ": ")


class CollaborationAPIHook(HTTPAPIHook):
    PREFIX = 'api'
    TYPES = ('recordingManager',)
    RE = r'createLink'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json',)
    COMMIT = True
    HTTP_POST = True

    def _hasAccess(self, aw):
        return RCCollaborationAdmin.hasRights(user=aw.getUser())

    def _getParams(self):

        super(CollaborationAPIHook, self)._getParams()
        self._indicoID = get_query_parameter(self._queryParams, ['iid', 'indicoID'])
        self._cdsID = get_query_parameter(self._queryParams, ['cid', 'cdsID'])

    def api_recordingManager(self, aw):
        if not self._indicoID or not self._cdsID:
            raise HTTPAPIError('A required argument is missing.', 400)

        success = createIndicoLink(self._indicoID, self._cdsID)
        return {'success': success}


class CollaborationExportHook(HTTPAPIHook):
    TYPES = ('eAgreements', )
    RE = r'(?P<confId>\w+)'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _hasAccess(self, aw):
        return RCCollaborationAdmin.hasRights(user=aw.getUser())

    def _getParams(self):
        super(CollaborationExportHook, self)._getParams()
        self._conf = ConferenceHolder().getById(self._pathParams['confId'], True)
        if not self._conf:
            raise HTTPAPIError('Conference does not exist.', 400)

    def export_eAgreements(self, aw):
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        requestType = CollaborationTools.getRequestTypeUserCanManage(self._conf, aw.getUser())
        contributions = manager.getContributionSpeakerByType(requestType)
        for cont, speakers in contributions.items():
            for spk in speakers:
                sw = manager.getSpeakerWrapperByUniqueId('%s.%s' % (cont, spk.getId()))
                if not sw:
                    continue
                signed = None
                if sw.getStatus() in (SpeakerStatusEnum.FROMFILE, SpeakerStatusEnum.SIGNED):
                    signed = True
                elif sw.getStatus() == SpeakerStatusEnum.REFUSED:
                    signed = False
                yield {
                    'confId': sw.getConference().getId(),
                    'contrib': cont,
                    'type': sw.getRequestType(),
                    'status': sw.getStatus(),
                    'signed': signed,
                    'speaker': {
                        'id': spk.getId(),
                        'name': spk.getFullName(),
                        'email': spk.getEmail()
                    }
                }


class VideoEventHook(HTTPAPIHook):
    """
    This has been defined as a separate hook to CollaborationExportHook et al
    due to the different input expected for both. It would be beneficial to
    find a way to amalgamate the two at a later date.
    """

    TYPES = ('video', )
    RE = r'(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'all'
    MAX_RECORDS = { # @TODO: Ascertain reasonable limits for each section.
        'all': 100000,
        'vidyo': 50000,
        'webcast': 50000,
        'mcu': 50000,
        'evo': 50000
    }
    GUEST_ALLOWED = False

    def _getParams(self):
        super(VideoEventHook, self)._getParams()

        """ In this case, idlist refers to the different indices which can
            be called, e.g: vidyo, evo, mcu etc.
        """
        self._idList = self._pathParams['idlist'].split('-')
        self._categ_id = get_query_parameter(self._queryParams, 'categ')

        if not self._queryParams.has_key('alarms'):
            self._alarms = None
        else:
            self._alarms = get_query_parameter(self._queryParams, ['alarms'], 0, True)

    def export_video(self, aw):
        expInt = VideoEventFetcher(aw, self)
        return expInt.video(self._idList, self._alarms, self._categ_id)


class VideoEventFetcher(IteratedDataFetcher):
    DETAIL_INTERFACES = {
        'all' : ICollaborationMetadataFossil
    }
    ID_TO_IDX = {
        'all' : 'all',
        'vidyo' : 'Vidyo',
        'webcast' : 'WebcastRequest',
        'recording' : 'RecordingRequest',
        'mcu' : 'CERNMCU',
        'evo' : 'EVO',
        'webex' : 'WebEx'
    }

    def __init__(self, aw, hook):
        super(VideoEventFetcher, self).__init__(aw, hook)
        self._alarm = None

    def _postprocess(self, obj, fossil, iface):
        if self._alarm is not None:
            fossil['alarm'] = self._alarm

        return fossil

    def iter_bookings(self, idList, categ_id=None):
        for vsid in idList:
            if vsid not in self.ID_TO_IDX:
                continue

            if vsid in ['webcast', 'recording']:
                idx = Catalog.getIdx('cs_booking_instance')[self.ID_TO_IDX[vsid]]
                for __, bkw in idx.iter_bookings(self._fromDT, self._toDT):
                    yield bkw
            else:
                idx = IndexesHolder().getById('collaboration');
                dateFormat = '%d/%m/%Y'

                tempBookings = idx.getBookings(self.ID_TO_IDX[vsid], "conferenceStartDate",
                                               self._orderBy, self._fromDT, self._toDT,
                                               'UTC', False, None, categ_id, False, dateFormat).getResults()

                for evt, bks in tempBookings:
                    for bk in bks:
                        bk._conf = evt # Ensure all CSBookings are aware of their Conference
                        yield bk


    def video(self, idList, alarm=None, categ_id=None):

        res = []
        bookings = []
        self._alarm = alarm


        """ Simple filter, as this method can return None for Pending and True
            for accepted, both are valid booking statuses for exporting.
        """
        def _filter(obj):
            return obj.getAcceptRejectStatus() is not False

        iface = self.DETAIL_INTERFACES.get('all')

        for booking in self._process(self.iter_bookings(idList, categ_id=categ_id), _filter, iface):
            yield booking
