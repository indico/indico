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

from indico.modules.events.registration.api import RHAPIRegistrant, RHAPIRegistrants
from indico.modules.events.registration.controllers.management.regform import (RHRegistrationFormList,
                                                                               RHRegistrationFormCreate,
                                                                               RHRegistrationFormEdit,
                                                                               RHRegistrationFormDelete)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('event_registration', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/registration', event_feature='registration')


# Management
_bp.add_url_rule('/manage/registration/', 'manage_regform_list', RHRegistrationFormList)
_bp.add_url_rule('/manage/registration/create', 'create_regform', RHRegistrationFormCreate, methods=('GET', 'POST'))

# Single registration form management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/edit',
                 'edit_regform', RHRegistrationFormEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/delete',
                 'delete_regform', RHRegistrationFormDelete, methods=('POST',))


# API
_bp.add_url_rule('!/api/events/<event_id>/registrants/<registrant_id>', 'api_registrant',
                 RHAPIRegistrant, methods=('GET', 'PATCH'))
_bp.add_url_rule('!/api/events/<event_id>/registrants', 'api_registrants',
                 RHAPIRegistrants)
