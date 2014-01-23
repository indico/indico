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

import requests
from MaKaC.plugins import PluginsHolder
from indico.modules.scheduler import PeriodicTask
from indico.ext.calendaring.storage import getAvatarConferenceStorage, isUserPluginEnabled
from indico.util.date_time import format_datetime
from webassets.filter.cssrewrite import urlpath
from indico.core.db import DBMgr
from MaKaC.common.externalOperationsManager import ExternalOperationsManager
from MaKaC.webinterface import urlHandlers

class OutlookUpdateCalendarNotificationTask(PeriodicTask):
    """
    A task that periodically updates notifications about events in regstrants/participants Outlook calendar
    """

    def run(self):
        logger = self.getLogger()
        storage = getAvatarConferenceStorage()
        keysToDelete = []

        # Send the requests
        for key, eventList in storage.iteritems():
            for event in eventList:
                logger.info("processing: %s:%s" % (key, event))
                if not event.get('request_sent', False): # only the ones that are not already sent
                    result = ExternalOperationsManager.execute(self, 'sendEventRequest' + key + event['eventType'], self._sendEventRequest, key, event['eventType'], event['avatar'], event['conference'])
                    if result != 200:
                        logger.debug("POST failed")
                        break
                    else:
                        logger.debug("processing successful")
                        event['request_sent'] = True
            else:
                keysToDelete.append(key)

        self._clearAvatarConferenceStorage(keysToDelete)

    def _clearAvatarConferenceStorage(self, keysToDelete):
        dbi = DBMgr.getInstance()
        dbi.commit() # Ensure that the status 'request_sent' is kept and requests are not sent twice
        storage = getAvatarConferenceStorage()
        for i, key in enumerate(keysToDelete):
            del storage[key]
            if i % 1000 == 999:
                dbi.commit()
        dbi.commit()

    def _sendEventRequest(self, key, eventType, avatar, conference):
        try:
            logger = self.getLogger()
            plugin = PluginsHolder().getPluginType('calendaring').getPlugin('outlook')
            if not isUserPluginEnabled(avatar.getId()):
                logger.info("outlook plugin disabled for user: %s" % avatar.getId())
                return 200
            if eventType in ['added', 'updated']:
                logger.debug("performing '%s' for: %s" % (eventType, avatar.getId()))
                url = urlHandlers.UHConferenceDisplay.getURL(conference)
                payload = {'userEmail': avatar.getEmail(),
                           'uniqueID': plugin.getOption('prefix').getValue() + key,
                           'subject': conference.getTitle(),
                           'location': conference.getRoom().getName() if conference.getRoom() else '',
                           'body': '<a href="%s">%s</a>' % (url, url) + '<br><br>' + conference.getDescription(),
                           'status': plugin.getOption('status').getValue(),
                           'startDate': format_datetime(conference.getStartDate(), format=plugin.getOption('datetimeFormat').getValue()),
                           'endDate': format_datetime(conference.getEndDate(), format=plugin.getOption('datetimeFormat').getValue()),
                           'isThereReminder': plugin.getOption('reminder').getValue(),
                           'reminderTimeInMinutes': plugin.getOption('reminder_minutes').getValue(),
                           }
                operation = plugin.getOption('addToCalendarOperationName').getValue() if eventType == 'added' else plugin.getOption('updateCalendarOperationName').getValue()
            elif eventType == 'removed':
                logger.debug("removing calendar entry for: %s" % avatar.getId())
                payload = {'userEmail': avatar.getEmail(),
                           'uniqueID': plugin.getOption('prefix').getValue() + key,
                           }
                operation = plugin.getOption('removeFromCalendarOperationName').getValue()
            else:
                return None
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            r = requests.post(urlpath.tslash(plugin.getOption('url').getValue()) + operation,
                              auth=(plugin.getOption('login').getValue(), plugin.getOption('password').getValue()),
                              data=payload, headers=headers, timeout=plugin.getOption('timeout').getValue())
            return r.status_code
        except requests.exceptions.Timeout:
            logger.exception('Timeout')
        except requests.exceptions.RequestException:
            logger.exception('RequestException: Connection problem')
        except Exception, e:
            logger.exception('Outlook EventException: %s' % e)
        return None

class OutlookTaskRegistry(object):

    @staticmethod
    def register(interval=15):
        from indico.modules.scheduler import Client
        from dateutil.rrule import MINUTELY
        from indico.core.db import DBMgr
        DBMgr.getInstance().startRequest()
        task = OutlookUpdateCalendarNotificationTask(MINUTELY, interval=interval)
        client = Client()
        client.enqueue(task)
        DBMgr.getInstance().endRequest()
