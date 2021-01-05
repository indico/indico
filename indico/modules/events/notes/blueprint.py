# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
