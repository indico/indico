# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from wtforms.fields.simple import HiddenField

from indico.modules.categories.models.event_move_request import EventMoveRequest, MoveRequestState
from indico.util.marshmallow import ModelList
from indico.web.forms.widgets import JinjaWidget


class CategoryField(HiddenField):
    """WTForms field that lets you select a category.

    :param require_event_creation_rights: Whether to allow selecting
                                          only categories where the
                                          user can create events.
    :param require_category_management_rights: Whether to allow selecting
                                               only categories where the
                                               user has management rights.
    :param show_event_creation_warning: Whether to show warning messages
                                        related to event creation.
    """

    widget = JinjaWidget('forms/category_picker_widget.html')

    def __init__(self, *args, require_event_creation_rights=False, require_category_management_rights=False,
                 show_event_creation_warning=False, **kwargs):
        self.navigator_category_id = None
        self.require_event_creation_rights = require_event_creation_rights
        self.require_category_management_rights = require_category_management_rights
        self.show_event_creation_warning = show_event_creation_warning
        super().__init__(*args, **kwargs)

    def process_data(self, value):
        if not value:
            self.data = None
            return
        self.data = value
        self.navigator_category_id = value.id

    def process_formdata(self, valuelist):
        from indico.modules.categories import Category
        if valuelist:
            try:
                category_id = int(json.loads(valuelist[0])['id'])
            except (KeyError, TypeError):
                self.data = None
            else:
                self.data = Category.get(category_id, is_deleted=False)

    def _value(self):
        return {'id': self.data.id, 'title': self.data.title} if self.data else {}

    def _get_data(self):
        return self.data


class EventRequestList(ModelList):
    def __init__(self, category, **kwargs):
        def _get_query(m):
            return m.query.filter(
                EventMoveRequest.category == category,
                EventMoveRequest.state == MoveRequestState.pending
            )
        super().__init__(model=EventMoveRequest, get_query=_get_query, collection_class=set, **kwargs)
