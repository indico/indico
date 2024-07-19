# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.controllers.admin import (RHAutoLinker, RHAutoLinkerConfig, RHCreateEventLabel,
                                                     RHCreateReferenceType, RHDataRetentionSettings, RHDeleteEventLabel,
                                                     RHDeleteReferenceType, RHEditEventLabel, RHEditReferenceType,
                                                     RHEventLabels, RHReferenceTypes, RHUnlistedEvents,
                                                     RHUpdateEventKeywords)
from indico.modules.events.controllers.api import RHEventCheckEmail, RHSingleEventAPI
from indico.modules.events.controllers.creation import RHCreateEvent, RHPrepareEvent
from indico.modules.events.controllers.display import (RHAutoLinkerRules, RHDisplayPrivacyPolicy, RHEventAccessKey,
                                                       RHExportEventICAL)
from indico.modules.events.controllers.entry import event_or_shorturl
from indico.web.flask.util import make_compat_redirect_func, redirect_view
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('events', __name__, template_folder='templates', virtual_template_folder='events')

# Admin
_bp.add_url_rule('/admin/external-id-types/', 'reference_types', RHReferenceTypes, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/external-id-types/create', 'create_reference_type', RHCreateReferenceType,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/admin/event-labels/', 'event_labels', RHEventLabels, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/event-labels/create', 'create_event_label', RHCreateEventLabel, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/event-keywords/', 'event_keywords', RHUpdateEventKeywords, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/unlisted-events/', 'unlisted_events', RHUnlistedEvents, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/autolinker/', 'autolinker_admin', RHAutoLinker)
_bp.add_url_rule('/admin/data-retention/', 'data_retention', RHDataRetentionSettings,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/admin/autolinker/config', 'autolinker_config', RHAutoLinkerConfig, methods=('POST',))

# Single reference type
_bp.add_url_rule('/admin/external-id-types/<int:reference_type_id>/edit', 'update_reference_type', RHEditReferenceType,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/admin/external-id-types/<int:reference_type_id>', 'delete_reference_type', RHDeleteReferenceType,
                 methods=('DELETE',))

# Single event label
_bp.add_url_rule('/admin/event-labels/<int:event_label_id>/edit', 'update_event_label', RHEditEventLabel,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/admin/event-labels/<int:event_label_id>', 'delete_event_label', RHDeleteEventLabel,
                 methods=('DELETE',))

# Auto-linker rules
_bp.add_url_rule('/api/autolinker-rules', 'autolinker_rules', RHAutoLinkerRules)

# Event ICS/iCal
_bp.add_url_rule('/event/<int:event_id>/event.ics', 'export_event_ical', RHExportEventICAL)

# Creation
_bp.add_url_rule('/event/create/<any(lecture,meeting,conference):event_type>', 'create', RHCreateEvent,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/event/create/prepare', 'prepare', RHPrepareEvent, methods=('POST',))

# Main entry points supporting shortcut URLs
# /e/ accepts slashes, /event/ doesn't - this is intended. We do not want to support slashes in the old namespace
# since it's a major pain in the ass to do so (and its route would eat anything that's usually a 404)
_bp.add_url_rule('/e/<path:event_id>', 'shorturl', event_or_shorturl, strict_slashes=False,
                 defaults={'shorturl_namespace': True})
# XXX: these two entries below use a string event_id on purpose, since they need to handle shortcuts
# and possibly legacy ids as well
_bp.add_url_rule('/event/<event_id>/', 'display', event_or_shorturl, strict_slashes=False)
_bp.add_url_rule('/event/<event_id>/overview', 'display_overview', event_or_shorturl,
                 defaults={'force_overview': True})
_bp.add_url_rule('/event/<int:event_id>/other-view', 'display_other', redirect_view('timetable.timetable'))

# Misc
_bp.add_url_rule('/event/<int:event_id>/key-access', 'key_access', RHEventAccessKey, methods=('POST',))
_bp.add_url_rule('/event/<int:event_id>/api/info-for-series', 'single_event_api', RHSingleEventAPI)

# Email checker for PersonLinkField
# Depending on where the person link is used, the person link field generates the correct url.
# Each object has its own url so that we can do proper access checks.
_event_object_url_prefixes = {
    'event': '',
    'session_block': '/sessions/<int:session_id>/blocks/<int:session_block_id>',
    'abstract': '/abstracts/<int:abstract_id>',
    'contribution': '/contributions/<int:contrib_id>',
    'subcontribution': '/contributions/<int:contrib_id>/subcontributions/<int:subcontrib_id>',
}
for object_type, prefix in _event_object_url_prefixes.items():
    _bp.add_url_rule(f'/event/<int:event_id>{prefix}/check-person-email', 'check_email',
                     RHEventCheckEmail, defaults={'object_type': object_type})


# Privacy policy
_bp.add_url_rule('/event/<int:event_id>/privacy', 'display_privacy', RHDisplayPrivacyPolicy)

# Legacy URLs
_compat_bp = IndicoBlueprint('compat_events', __name__)
_compat_bp.add_url_rule('/conferenceDisplay.py', 'display_modpython',
                        make_compat_redirect_func(_bp, 'display', view_args_conv={'confId': 'event_id'}))
_compat_bp.add_url_rule('/conferenceOtherViews.py', 'display_other_modpython',
                        make_compat_redirect_func(_bp, 'display_other', view_args_conv={'confId': 'event_id'}))
_compat_bp.add_url_rule('/conferenceDisplay.py/overview', 'display_overview_modpython',
                        make_compat_redirect_func(_bp, 'display_overview', view_args_conv={'confId': 'event_id'}))
_compat_bp.add_url_rule('/event/<int:event_id>/my-conference/', 'display_mystuff',
                        make_compat_redirect_func(_bp, 'display', view_args_conv={'confId': 'event_id'}))
_compat_bp.add_url_rule('/myconference.py', 'display_mystuff_modpython',
                        make_compat_redirect_func(_bp, 'display', view_args_conv={'confId': 'event_id'}))
