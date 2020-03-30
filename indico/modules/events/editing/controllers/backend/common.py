# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core import signals
from indico.modules.events.editing.controllers.base import RHEditingBase
from indico.modules.events.editing.schemas import EditingFileTypeSchema, EditingMenuItemSchema, EditingTagSchema
from indico.util.signals import named_objects_from_signal


class RHEditingFileTypes(RHEditingBase):
    """Return all editing file types defined in the event."""

    def _process(self):
        return EditingFileTypeSchema(many=True).jsonify(self.event.editing_file_types)


class RHEditingTags(RHEditingBase):
    """Return all editing tags defined in the event."""

    def _process(self):
        return EditingTagSchema(many=True).jsonify(self.event.editing_tags)


class RHMenuEntries(RHEditingBase):
    """Return the menu entries for the editing view."""

    def _process(self):
        menu_entries = named_objects_from_signal(signals.menu.items.send('event-editing-sidemenu', event=self.event))
        return EditingMenuItemSchema(many=True).jsonify(menu_entries.values())
