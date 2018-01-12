# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.events import event_object_url_prefixes
from indico.modules.events.notes.controllers import RHCompileNotes, RHDeleteNote, RHEditNote, RHViewNote
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_notes', __name__, template_folder='templates', virtual_template_folder='events/notes',
                      url_prefix='/event/<confId>')

_bp.add_url_rule('/note/compile', 'compile', RHCompileNotes, methods=('GET', 'POST'), defaults={'object_type': 'event'})


for object_type, prefixes in event_object_url_prefixes.iteritems():
    for prefix in prefixes:
        _bp.add_url_rule(prefix + '/note/', 'view', RHViewNote, defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/note/edit', 'edit', RHEditNote, methods=('GET', 'POST'),
                         defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/note/delete', 'delete', RHDeleteNote, methods=('POST',),
                         defaults={'object_type': object_type})
