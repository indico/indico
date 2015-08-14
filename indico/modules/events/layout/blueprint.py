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

from indico.web.flask.wrappers import IndicoBlueprint
from indico.modules.events.layout.controllers import (RHLayoutEdit, RHLayoutLogoUpload, RHLogoDisplay, RHMenuAddEntry,
                                                      RHMenuDeleteEntry, RHMenuEdit, RHMenuEnableEntry, RHMenuEntryEdit,
                                                      RHMenuEntryPosition)

_bp = IndicoBlueprint('event_layout', __name__, template_folder='templates',
                      virtual_template_folder='events/layout', url_prefix='/event/<confId>/manage/layout')

_bp.add_url_rule('/', 'index', RHLayoutEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/logo/upload', 'logo-upload', RHLayoutLogoUpload, methods=('POST',))
_bp.add_url_rule('/menu/', 'menu', RHMenuEdit)
_bp.add_url_rule('/menu/<int:menu_entry_id>/', 'menu-entry-edit', RHMenuEntryEdit, methods=('GET', 'POST',))
_bp.add_url_rule('/menu/<int:menu_entry_id>/position', 'menu-entry-position', RHMenuEntryPosition, methods=('POST',))
_bp.add_url_rule('/menu/<int:menu_entry_id>/enable', 'menu-enable-entry', RHMenuEnableEntry, methods=('POST',))
_bp.add_url_rule('/menu/<int:menu_entry_id>/delete', 'menu-delete-entry', RHMenuDeleteEntry, methods=('DELETE',))
_bp.add_url_rule('/menu/add', 'menu-add-entry', RHMenuAddEntry, methods=('GET', 'POST'))


_bp_images = IndicoBlueprint('event_images', __name__, template_folder='templates',
                             virtual_template_folder='events/layout', url_prefix='/event/<confId>')
_bp_images.add_url_rule('/logo', 'logo-display', RHLogoDisplay, methods=('GET',))
