# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from itertools import chain

from indico.core.db.sqlalchemy.custom.unaccent import unaccent_match
from indico.modules.groups import GroupProxy
from indico.modules.events.models.events import Event
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.util import serialize_event_person
from indico.modules.users.legacy import search_avatars
from indico.util.string import to_unicode, sanitize_email
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.user import IGroupFossil
from MaKaC.services.implementation.base import LoggedOnlyService


class SearchBase(LoggedOnlyService):
    CHECK_HTML = False

    def _checkParams(self):
        self._searchExt = self._params.get('search-ext', False)


class SearchUsers(SearchBase):
    def _checkParams(self):
        SearchBase._checkParams(self)
        self._surName = self._params.get("surName", "")
        self._name = self._params.get("name", "")
        self._organisation = self._params.get("organisation", "")
        self._email = sanitize_email(self._params.get("email", ""))
        self._exactMatch = self._params.get("exactMatch", False)
        self._confId = self._params.get("conferenceId", None)
        self._event = Event.get(self._confId, is_deleted=False) if self._confId else None

    def _getAnswer(self):
        event_persons = []
        criteria = {
            'surName': self._surName,
            'name': self._name,
            'organisation': self._organisation,
            'email': self._email
        }
        users = search_avatars(criteria, self._exactMatch, self._searchExt)
        if self._event:
            fields = {EventPerson.first_name: self._name,
                      EventPerson.last_name: self._surName,
                      EventPerson.email: self._email,
                      EventPerson.affiliation: self._organisation}
            criteria = [unaccent_match(col, val, exact=self._exactMatch) for col, val in fields.iteritems()]
            event_persons = self._event.persons.filter(*criteria).all()
        fossilized_users = fossilize(sorted(users, key=lambda av: (av.getStraightFullName(), av.getEmail())))
        fossilized_event_persons = map(serialize_event_person, event_persons)
        unique_users = {to_unicode(user['email']): user for user in chain(fossilized_users, fossilized_event_persons)}
        return sorted(unique_users.values(), key=lambda x: (to_unicode(x['name']).lower(), to_unicode(x['email'])))


class SearchGroups(SearchBase):

    def _checkParams(self):
        SearchBase._checkParams(self)
        self._group = self._params.get("group", "").strip()
        self._exactMatch = self._params.get("exactMatch", False)

    def _getAnswer(self):
        results = [g.as_legacy_group for g in GroupProxy.search(self._group, exact=self._exactMatch)]
        fossilized_results = fossilize(results, IGroupFossil)
        for fossilizedGroup in fossilized_results:
            fossilizedGroup["isGroup"] = True
        return fossilized_results


methodMap = {
    "users": SearchUsers,
    "groups": SearchGroups,
}
