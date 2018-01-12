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

from indico.modules.events.controllers.admin import (RHCreateReferenceType, RHDeleteReferenceType, RHEditReferenceType,
                                                     RHReferenceTypes)
from indico.modules.events.controllers.creation import RHCreateEvent
from indico.modules.events.controllers.display import RHEventAccessKey, RHEventMarcXML, RHExportEventICAL
from indico.modules.events.controllers.entry import event_or_shorturl
from indico.web.flask.util import make_compat_redirect_func, redirect_view
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('events', __name__, template_folder='templates', virtual_template_folder='events')

# Admin
_bp.add_url_rule('/admin/external-id-types/', 'reference_types', RHReferenceTypes, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/external-id-types/create', 'create_reference_type', RHCreateReferenceType,
                 methods=('GET', 'POST'))

# Single reference type
_bp.add_url_rule('/admin/external-id-types/<int:reference_type_id>/edit', 'update_reference_type', RHEditReferenceType,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/admin/external-id-types/<int:reference_type_id>', 'delete_reference_type', RHDeleteReferenceType,
                 methods=('DELETE',))

_bp.add_url_rule('/event/<confId>/event.ics', 'export_event_ical', RHExportEventICAL)

# Creation
_bp.add_url_rule('/event/create/<any(lecture,meeting,conference):event_type>', 'create', RHCreateEvent,
                 methods=('GET', 'POST'))

# Main entry points supporting shortcut URLs
# /e/ accepts slashes, /event/ doesn't - this is intended. We do not want to support slashes in the old namespace
# since it's a major pain in the ass to do so (and its route would eat anything that's usually a 404)
_bp.add_url_rule('/e/<path:confId>', 'shorturl', event_or_shorturl, strict_slashes=False,
                 defaults={'shorturl_namespace': True})
_bp.add_url_rule('/event/<confId>/', 'display', event_or_shorturl)
_bp.add_url_rule('/event/<confId>/overview', 'display_overview', event_or_shorturl, defaults={'force_overview': True})
_bp.add_url_rule('/event/<confId>/other-view', 'display_other', redirect_view('timetable.timetable'))

# Misc
_bp.add_url_rule('/event/<confId>/key-access', 'key_access', RHEventAccessKey, methods=('POST',))
_bp.add_url_rule('/event/<confId>/event.marc.xml', 'marcxml', RHEventMarcXML)


# Legacy URLs
_compat_bp = IndicoBlueprint('compat_events', __name__)
_compat_bp.add_url_rule('/conferenceDisplay.py', 'display_modpython', make_compat_redirect_func(_bp, 'display'))
_compat_bp.add_url_rule('/conferenceOtherViews.py', 'display_other_modpython',
                        make_compat_redirect_func(_bp, 'display_other'))
_compat_bp.add_url_rule('/conferenceDisplay.py/overview', 'display_overview_modpython',
                        make_compat_redirect_func(_bp, 'display_overview'))
_compat_bp.add_url_rule('/event/<confId>/my-conference/', 'display_mystuff', make_compat_redirect_func(_bp, 'display'))
_compat_bp.add_url_rule('/myconference.py', 'display_mystuff_modpython', make_compat_redirect_func(_bp, 'display'))
