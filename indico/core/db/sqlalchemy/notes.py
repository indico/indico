# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.notes.models.notes import EventNote
from indico.modules.events.notes.util import can_edit_note
from indico.util.caching import memoize_request


class AttachedNotesMixin(object):
    """
    Allow for easy retrieval of structured information about
    items attached to the object.
    """
    # When set to ``True`` .has_note preload all notes that exist for the same event
    # Should be set to False when not applicable (no object.event property)
    PRELOAD_EVENT_NOTES = False

    @property
    @memoize_request
    def has_note(self):
        return EventNote.get_for_linked_object(self, preload_event=self.PRELOAD_EVENT_NOTES) is not None

    def can_edit_note(self, user):
        return can_edit_note(self, user)
