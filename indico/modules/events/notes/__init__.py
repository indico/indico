# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.core.logger import Logger


logger = Logger.get('events.notes')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.events.notes.models.notes import EventNoteRevision
    EventNoteRevision.find(user_id=source.id).update({EventNoteRevision.user_id: target.id})


@signals.event_management.get_cloners.connect
def _get_attachment_cloner(sender, **kwargs):
    from indico.modules.events.notes.clone import NoteCloner
    return NoteCloner
