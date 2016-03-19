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

from __future__ import unicode_literals

from itertools import islice
from operator import attrgetter

from indico.modules.events.agreements.util import get_agreement_definitions
from indico.web.http_api import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError
from MaKaC.conference import ConferenceHolder


@HTTPAPIHook.register
class AgreementExportHook(HTTPAPIHook):
    TYPES = ('agreements',)
    RE = r'(?P<agreement_type>[^/]+)/(?P<event_id>\w+)'
    MAX_RECORDS = {}
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json', 'jsonp', 'xml')

    def _getParams(self):
        super(AgreementExportHook, self)._getParams()
        type_ = self._pathParams['agreement_type']
        try:
            self._definition = get_agreement_definitions()[type_]
        except KeyError:
            raise HTTPAPIError('No such agreement type', 404)
        self._event = ConferenceHolder().getById(self._pathParams['event_id'], True)
        if self._event is None:
            raise HTTPAPIError('No such event', 404)

    def _hasAccess(self, aw):
        return self._definition.can_access_api(aw.getUser().user, self._event.as_event)

    def export_agreements(self, aw):
        event = self._event.as_event
        sent_agreements = {a.identifier: a for a in event.agreements.filter_by(type=self._definition.name)}
        for person in islice(sorted(self._definition.get_people(event).itervalues(),
                                    key=attrgetter('name', 'identifier')),
                             self._offset, self._offset + self._limit):
            agreement = sent_agreements.get(person.identifier)
            data = {
                'event_id': event.id,
                'identifier': person.identifier,
                'sent': agreement is not None,
                'accepted': None if (not agreement or agreement.pending) else agreement.accepted,
            }
            self._definition.extend_api_data(event, person, agreement, data)
            yield data
