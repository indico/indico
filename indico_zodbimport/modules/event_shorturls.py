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

from __future__ import unicode_literals, division

import re

from sqlalchemy.orm.exc import NoResultFound

from indico.core.db import db
from indico.modules.events import LegacyEventMapping
from indico.modules.events.models.events import Event
from indico.util.console import verbose_iterator, cformat
from indico.util.struct.iterables import committing_iterator

from indico_zodbimport import Importer
from indico_zodbimport import convert_to_unicode


class EventShorturlsImporter(Importer):
    def has_data(self):
        return Event.query.filter(Event.url_shortcut != '').has_rows()

    def migrate(self):
        self.legacy_event_ids = {x for x, in db.session.query(LegacyEventMapping.legacy_event_id)}
        self.migrate_event_shorturls()

    def _validate_shorturl(self, shorturl):
        if shorturl.isdigit():
            return 'only-digits'
        if 'http://' in shorturl or 'https://' in shorturl:
            return 'url'
        # XXX: we allow spaces and similar harmless garbage here. it's awful but no need in breaking existing urls
        if not re.match(r'^[-a-zA-Z0-9/._ &@]+$', shorturl) or '//' in shorturl:
            return 'invalid-chars'
        if shorturl[0] == '/':
            return 'leading-slash'
        if shorturl[-1] == '/':
            return 'trailing-slash'
        if shorturl in self.legacy_event_ids:
            return 'legacy-id'
        return None

    def migrate_event_shorturls(self):
        self.print_step("Migrating event shorturls")
        todo = {}
        done = {}
        for shorturl, conf, event in self._iter_shorturls():
            shorturl = convert_to_unicode(shorturl)
            event_shorturl = convert_to_unicode(conf._sortUrlTag)
            if event_shorturl.lower() != shorturl.lower():
                # warn about mismatch but keep the one from the mapping.
                # this is a bit weird but like this we never risk breaking urls
                self.print_warning(cformat('%{yellow}Shorturl %{yellow!}{}%{reset}%{yellow} from mapping not matching '
                                           'event shorturl %{yellow!}{}%{reset}%{yellow}')
                                   .format(shorturl, event_shorturl), event_id=event.id)
            error = self._validate_shorturl(shorturl)
            if error == 'url':
                # show obvious garbage in a less prominent way
                self.print_warning(cformat('%{yellow}Shorturl %{yellow!}{}%{reset}%{yellow} is invalid: %{yellow!}{}')
                                   .format(shorturl, error), event_id=event.id)
                continue
            elif error:
                self.print_warning(cformat('%{red}Shorturl %{yellow!}{}%{reset}%{red} is invalid: %{red!}{}')
                                   .format(shorturl, error), event_id=event.id)
                continue
            conflict = done.get(shorturl.lower())
            if conflict and conflict[1] != event:
                # if there's a conflict caused by the previously case-sensitive url shortcuts,
                # discard them in both events - it's better to get a 404 error than a wrong event
                self.print_error(cformat('%{red!}Shorturl %{reset}%{red}{}%{red!} collides with '
                                         '%{reset}%{red}{}%{red!} in event %{reset}%{red}{}%{red!}; discarding both')
                                 .format(shorturl, conflict[0], conflict[1]), event_id=event.id)
                del done[shorturl.lower()]
                del todo[conflict[1]]
                continue
            done[shorturl.lower()] = (shorturl, event)
            todo[event] = shorturl

        it = verbose_iterator(todo.iteritems(), len(todo), lambda x: x[0].id, lambda x: '')
        for event, shorturl in committing_iterator(it):
            event.url_shortcut = shorturl
            self.print_success('{} -> {}'.format(shorturl, event.title), event_id=event.id)

    def _iter_shorturls(self):
        it = self.zodb_root['shorturl'].iteritems()
        total = len(self.zodb_root['shorturl'])
        it = verbose_iterator(it, total, lambda x: x[1].id, lambda x: '')
        for shorturl, conf in it:
            try:
                event = Event.get_one(conf.id)
            except NoResultFound:
                self.print_warning(cformat('%{yellow!}Ignoring shorturl %{reset}%{yellow}{}%{yellow!} (event deleted)')
                                   .format(shorturl), always=False, event_id=conf.id)
                continue
            yield shorturl, conf, event
