# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.persons.controllers import (RHAPIEmailEventPersonsMetadata, RHAPIEmailEventPersonsSend,
                                                       RHDeleteUnusedEventPerson, RHEmailEventPersonsPreview,
                                                       RHEventPersonSearch, RHGrantModificationRights,
                                                       RHGrantSubmissionRights, RHManagePersonLists, RHPersonsList,
                                                       RHRevokeSubmissionRights, RHSyncEventPerson, RHUpdateEventPerson)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('persons', __name__, template_folder='templates', virtual_template_folder='events/persons',
                      url_prefix='/event/<int:event_id>/manage')

_bp.add_url_rule('/persons/', 'person_list', RHPersonsList)
_bp.add_url_rule('/api/persons/email/send', 'api_email_event_persons_send', RHAPIEmailEventPersonsSend,
                 methods=('POST',))
_bp.add_url_rule('/api/persons/email/metadata', 'api_email_event_persons_metadata', RHAPIEmailEventPersonsMetadata,
                 methods=('POST',))
_bp.add_url_rule('/api/persons/email/preview', 'email_event_persons_preview', RHEmailEventPersonsPreview,
                 methods=('POST',))
_bp.add_url_rule('/persons/grant-submission', 'grant_submission_rights', RHGrantSubmissionRights, methods=('POST',))
_bp.add_url_rule('/persons/grant-modification', 'grant_modification_rights', RHGrantModificationRights,
                 methods=('POST',))
_bp.add_url_rule('/persons/revoke-submission', 'revoke_submission_rights', RHRevokeSubmissionRights,
                 methods=('POST',))


# EventPerson operations
_bp.add_url_rule('/persons/<int:person_id>', 'update_person', RHUpdateEventPerson, methods=('PATCH',))
_bp.add_url_rule('/persons/<int:person_id>/sync', 'sync_with_user', RHSyncEventPerson, methods=('POST',))
_bp.add_url_rule('/persons/<int:person_id>', 'delete_unused_person', RHDeleteUnusedEventPerson, methods=('DELETE',))
_bp.add_url_rule('/api/persons/search', 'event_person_search', RHEventPersonSearch)


# Manage person list settings
_bp.add_url_rule('/persons/person-lists', 'manage_person_lists', RHManagePersonLists, methods=('GET', 'POST'))
