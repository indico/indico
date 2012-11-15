# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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
from indico.ext.calendaring.storage import getAvatarConferenceStorage, clearAvatarConferenceStorage, isUserPluginEnabled
from indico.util.date_time import format_datetime
from webassets.filter.cssrewrite import urlpath


class OutlookUpdateCalendarNotificationTask(PeriodicTask):
    """
    A task that periodically updates notifications about events in regstrants/participants Outlook calendar
    """

    def run(self):
        logger = self.getLogger()
        plugin = PluginsHolder().getPluginType('calendaring').getPlugin('outlook')
        storage = getAvatarConferenceStorage()
        keysToDelete = []
        for key, eventList in storage.iteritems():
            success = True
            for event in eventList:
                logger.info("processing: %s:%s" % (key, event))
                if self._sendEventRequest(key, event['eventType'], event['avatar'], event['conference'], plugin) is 200:
                    logger.info("processing successful")
                    event['eventType'] = "toDelete"
                else:
                    success = False
                    logger.info("processing failed")
            if success:
                keysToDelete.append(key)
        clearAvatarConferenceStorage(keysToDelete)

    def _sendEventRequest(self, key, eventType, avatar, conference, plugin):
        try:
            logger = self.getLogger()
            if not isUserPluginEnabled(avatar.getId()):
                logger.info("outlook plugin disabled for user: %s" % avatar.getId())
                return 200
            if eventType == 'added':
                logger.debug("adding new calendar entry for: %s" % avatar.getId())
                payload = {'userEmail': avatar.getEmail(),
                           'uniqueID': plugin.getOption('prefix').getValue() + key,
                           'subject': conference.getTitle(),
                           'location': conference.getRoom().getFullName(),
                           'body': conference.getDescription(),
                           'status': plugin.getOption('status').getValue(),
                           'startDate': format_datetime(conference.getStartDate(), format=plugin.getOption('timeFormat').getValue()),
                           'endDate': format_datetime(conference.getEndDate(), format=plugin.getOption('timeFormat').getValue()),
                           'isThereReminder': plugin.getOption('reminder').getValue(),
                           'reminderTimeInMinutes': plugin.getOption('reminder_minutes').getValue(),
                           }
                operation = plugin.getOption('addToCalendarOperationName').getValue()
            elif eventType == 'updated':
                logger.debug("updating calendar entry for: %s" % avatar.getId())
                payload = {'userEmail': avatar.getEmail(),
                           'uniqueID': plugin.getOption('prefix').getValue() + key,
                           'subject': conference.getTitle(),
                           'location': conference.getRoom().getFullName(),
                           'body': conference.getDescription(),
                           'status': plugin.getOption('status').getValue(),
                           'startDate': format_datetime(conference.getStartDate(), format=plugin.getOption('timeFormat').getValue()),
                           'endDate': format_datetime(conference.getEndDate(), format=plugin.getOption('timeFormat').getValue()),
                           'isThereReminder': plugin.getOption('reminder').getValue(),
                           'reminderTimeInMinutes': plugin.getOption('reminder_minutes').getValue(),
                           }
                operation = plugin.getOption('updateCalendarOperationName').getValue()
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
            logger.exception('RequestException: Timeout')
        except requests.exceptions.RequestException:
            logger.exception('RequestException: Connection problem')
        except Exception, e:
            logger.exception('SendEventException: %s' % e)
        return None
