# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json

from wtforms.fields.simple import HiddenField

from indico.web.forms.widgets import JinjaWidget


class CategoryField(HiddenField):
    """WTForms field that lets you select a category.

    :param require_event_creation_rights: Whether to allow selecting
                                          only categories where the
                                          user can create events.
    """

    widget = JinjaWidget('forms/category_picker_widget.html')

    def __init__(self, *args, **kwargs):
        self.navigator_category_id = 0
        self.require_event_creation_rights = kwargs.pop('require_event_creation_rights', False)
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
            except KeyError:
                self.data = None
            else:
                self.data = Category.get(category_id, is_deleted=False)

    def _value(self):
        return {'id': self.data.id, 'title': self.data.title} if self.data else {}

    def _get_data(self):
        return self.data
