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

from __future__ import unicode_literals

from indico.modules.events.persons.controllers import (RHPersonsList, RHEmailEventPersons, RHGrantSubmissionRights,
                                                       RHGrantModificationRights, RHRevokeSubmissionRights,
                                                       RHEditEventPerson)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('persons', __name__, template_folder='templates', virtual_template_folder='events/persons',
                      url_prefix='/event/<confId>/manage')

_bp.add_url_rule('/persons/', 'person_list', RHPersonsList)
_bp.add_url_rule('/persons/email', 'email_event_persons', RHEmailEventPersons, methods=('POST',))
_bp.add_url_rule('/persons/grant-submission', 'grant_submission_rights', RHGrantSubmissionRights, methods=('POST',))
_bp.add_url_rule('/persons/grant-modification', 'grant_modification_rights', RHGrantModificationRights,
                 methods=('POST',))
_bp.add_url_rule('/persons/revoke-submission', 'revoke_submission_rights', RHRevokeSubmissionRights,
                 methods=('POST',))


# EventPerson operations
_bp.add_url_rule('/persons/<int:person_id>/edit', 'edit_person', RHEditEventPerson, methods=('GET', 'POST'))
