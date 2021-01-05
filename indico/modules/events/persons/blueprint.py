# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.persons.controllers import (RHEditEventPerson, RHEmailEventPersons,
                                                       RHGrantModificationRights, RHGrantSubmissionRights,
                                                       RHPersonsList, RHRevokeSubmissionRights)
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
