# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2011 CERN.
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

import icalendar as ical

from indico.web.http_api import HTTPAPIHook, DataFetcher
from indico.web.http_api.ical import ICalSerializer
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache
from indico.util.fossilize import fossilize, IFossil
from indico.util.fossilize.conversion import Conversion

from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin
from MaKaC.common.indexes import IndexesHolder
from MaKaC.plugins.Collaboration.RecordingManager.common import createIndicoLink
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.conference import ConferenceHolder
from MaKaC.plugins.Collaboration.base import SpeakerStatusEnum
from MaKaC.plugins.Collaboration.fossils import ICollaborationMetadataFossil


globalHTTPAPIHooks = ['CollaborationAPIHook', 'CollaborationExportHook', 'VideoEventHook']


def serialize_collaboration_alarm(fossil, now):
    alarm = ical.Alarm()
    trigger = "-PT" + str(fossil['alarm']) + "M"  # iCalendar spec for pre-event trigger
    alarm.set('trigger', trigger)
    alarm.set('action', 'DISPLAY')
    alarm.set('summary', "[" + fossil['type'] + "] " + fossil['status'] + " - " + fossil['title'].decode('utf-8'))
    alarm.set('description', str(fossil['url']))
    return alarm


def serialize_collaboration(fossil, now):
    event = ical.Event()
    url = str(fossil['url'])
    event.set('uid', 'indico-collaboration-%s@cern.ch' % fossil['uniqueId'])
    event.set('dtstamp', now)
    event.set('dtstart', fossil['startDate'])
    event.set('dtend', fossil['endDate'])
    event.set('url', url)
    event.set('categories', "VideoService - " + fossil['type'])
    event.set('summary', "[" + fossil['type'] + "] " + fossil['status'] + " - " + fossil['title'].decode('utf-8'))
    event.set('description', url)

    # If there is an alarm required, add a subcomponent to the Event
    if fossil.has_key('alarm'):
        event.add_component(serialize_collaboration_alarm(fossil, now))

    return event


# the iCal serializer needs some extra info on how to display things
ICalSerializer.register_mapper('collaborationMetadata', serialize_collaboration)


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
            raise HTTPAPIError('A required argument is missing.', apache.HTTP_BAD_REQUEST)

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
            raise HTTPAPIError('Conference does not exist.', apache.HTTP_BAD_REQUEST)

    def export_eAgreements(self, aw):
        manager = self._conf.getCSBookingManager()
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

    def _getParams(self):
        super(VideoEventHook, self)._getParams()

        """ In this case, idlist refers to the different indicies which can
            be called, e.g: vidyo, evo, mcu etc.
        """
        self._idList = self._pathParams['idlist'].split('-')

        if not self._queryParams.has_key('alarms'):
            self._alarms = None
        else:
            self._alarms = get_query_parameter(self._queryParams, ['alarms'], 0, True)

    def export_video(self, aw):
        expInt = VideoEventFetcher(aw, self)
        return expInt.video(self._idList, self._alarms)


class VideoEventFetcher(DataFetcher):
    DETAIL_INTERFACES = {
        'all' : ICollaborationMetadataFossil
    }
    ID_TO_IDX = {
        'all' : 'all',
        'vidyo' : 'Vidyo',
        'webcast' : 'WebcastRequest',
        'recording' : 'RecordingRequest',
        'mcu' : 'CERNMCU',
        'evo' : 'EVO'
    }

    def __init__(self, aw, hook):
        super(VideoEventFetcher, self).__init__(aw, hook)
        self._alarm = None

    def _postprocess(self, obj, fossil, iface):
        if self._alarm is not None:
            fossil['alarm'] = self._alarm

        return fossil

    def video(self, idList, alarm = None):
        idx = IndexesHolder().getById('collaboration');
        bookings = []
        dateFormat = '%d/%m/%Y'
        self._alarm = alarm

        for id in idList:
            tempBookings = idx.getBookings(self.ID_TO_IDX[id], "conferenceStartDate",
                                           self._orderBy, self._fromDT, self._toDT,
                                           'UTC', False, None, None, False, dateFormat)
            bookings.extend(tempBookings.getResults())

        """ Iterate the bookings and yield the results for fossilization, the form
            by this point should be objs[i] = tuple('arranger', [CSBooking Objects]).
        """
        def _iter_bookings(objs):
            for obj in objs:
                for bk in obj[1]:
                    bk._conf = obj[0] # Ensure all CSBookings are aware of their Conference

                    """ This is for plugins whose structure include 'talkSelected',
                        examples of which in CERN Indico being WebcastRequest and
                        RecordingRequest.
                    """
                    if bk.hasTalkSelection():
                        ts = bk.getTalkSelectionList()
                        contributions = []

                        if ts is None: # No individual talks, therefore an event for every contribution
                            contributions = bk._conf.getContributionList()
                        else:
                            for contribId in ts:
                                tempContrib = bk._conf.getContributionById(contribId)
                                contributions.append(tempContrib)

                        if len(contributions) == 0: # If we are here, no contributions but a request exists.
                            bk.setStartDate(bk._conf.getStartDate())
                            bk.setEndDate(bk._conf.getEndDate())
                            yield bk
                        else: # contributions is the list of all to be exported now
                            for contrib in contributions:
                                if contrib.isScheduled():
                                    bk.setStartDate(contrib.getStartDate())
                                    bk.setEndDate(contrib.getEndDate())
                                else:
                                    bk.setStartDate(bk._conf.getStartDate())
                                    bk.setEndDate(bk._conf.getEndDate())
                                yield bk

                        continue

                    yield bk

        """ Simple filter, as this method can return None for Pending and True
            for accepted, both are valid booking statuses for exporting.
        """
        def filter(obj):
            return obj.getAcceptRejectStatus() is not False

        iface = self.DETAIL_INTERFACES.get('all')

        for booking in self._process(_iter_bookings(bookings), filter, iface):
            yield booking
