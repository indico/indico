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

from indico.modules.events.controllers.admin import (RHReferenceTypes, RHCreateReferenceType, RHEditReferenceType,
                                                     RHDeleteReferenceType)
from indico.modules.events.controllers.management import RHManageReferences, RHManageEventLocation
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

_bp.add_url_rule('/event/<confId>/manage/external-ids', 'manage_event_references', RHManageReferences,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/event-location', 'manage_event_location', RHManageEventLocation,
                 methods=('GET', 'POST'))
