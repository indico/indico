# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events import event_object_url_prefixes
from indico.modules.events.notes.controllers import RHApiCompileNotes, RHApiNote, RHGotoNote, RHViewNote
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_notes', __name__, template_folder='templates', virtual_template_folder='events/notes',
                      url_prefix='/event/<int:event_id>')

_bp.add_url_rule('/api/scheduled-notes', 'compile', RHApiCompileNotes, defaults={'object_type': 'event'})


for object_type, prefixes in event_object_url_prefixes.items():
    for prefix in prefixes:
        _bp.add_url_rule(prefix + '/note/', 'view', RHViewNote, defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/api/note', 'api', RHApiNote, methods=('GET', 'POST', 'DELETE'),
                         defaults={'object_type': object_type})

_bp.add_url_rule('/note/<int:note_id>', 'goto', RHGotoNote)
