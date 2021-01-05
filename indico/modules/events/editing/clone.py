# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.cloning import EventCloner
from indico.modules.events.editing.models.file_types import EditingFileType
from indico.modules.events.editing.models.review_conditions import EditingReviewCondition
from indico.modules.events.editing.models.tags import EditingTag
from indico.modules.events.models.events import EventType
from indico.util.i18n import _


class EditingSettingsCloner(EventCloner):
    name = 'editing_settings'
    friendly_name = _('Editing (configured tags, file types, review conditions)')
    new_event_only = True

    @property
    def is_visible(self):
        return self.old_event.type_ == EventType.conference

    @no_autoflush
    def run(self, new_event, cloners, shared_data, event_exists=False):
        self._filetype_map = {}
        self._clone_tags(new_event)
        self._clone_filetypes(new_event)
        self._clone_review_conditions(new_event)
        db.session.flush()

    def _clone_tags(self, new_event):
        attrs = get_simple_column_attrs(EditingTag)
        for old_tag in self.old_event.editing_tags:
            tag = EditingTag()
            tag.populate_from_attrs(old_tag, attrs)
            new_event.editing_tags.append(tag)

    def _clone_filetypes(self, new_event):
        attrs = get_simple_column_attrs(EditingFileType)
        del new_event.editing_file_types[:]
        db.session.flush()
        for old_filetype in self.old_event.editing_file_types:
            filetype = EditingFileType()
            filetype.populate_from_attrs(old_filetype, attrs)
            new_event.editing_file_types.append(filetype)
            db.session.flush()
            self._filetype_map[old_filetype] = filetype

    def _clone_review_conditions(self, new_event):
        old_conditions = EditingReviewCondition.query.with_parent(self.old_event).all()
        for condition in old_conditions:
            new_filetypes = {self._filetype_map[ft] for ft in condition.file_types}
            new_condition = EditingReviewCondition(type=condition.type, file_types=new_filetypes)
            new_event.editing_review_conditions.append(new_condition)
