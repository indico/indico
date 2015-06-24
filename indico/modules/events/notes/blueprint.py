# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.notes.controllers import RHEditNote, RHDeleteNote
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_notes', __name__, template_folder='templates', virtual_template_folder='events/notes',
                      url_prefix='/event/<confId>')

_bp.add_url_rule('/note/', 'edit', RHEditNote, methods=('GET', 'POST', 'DELETE'), defaults={'object_type': 'event'})
_bp.add_url_rule('/note/delete', 'delete', RHDeleteNote, methods=('POST',), defaults={'object_type': 'event'})

_bp.add_url_rule('/session/<sessionId>/note/', 'edit', RHEditNote, defaults={'object_type': 'session'},
                 methods=('GET', 'POST', 'DELETE'))

with _bp.add_prefixed_rules('/session/<sessionId>'):
    _bp.add_url_rule('/contribution/<contribId>/note/', 'edit', RHEditNote, defaults={'object_type': 'contribution'},
                     methods=('GET', 'POST', 'DELETE'))
    _bp.add_url_rule('/contribution/<contribId>/<subContId>/note/', 'edit', RHEditNote,
                     defaults={'object_type': 'subcontribution'}, methods=('GET', 'POST', 'DELETE'))
