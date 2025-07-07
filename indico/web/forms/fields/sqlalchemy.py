# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from operator import attrgetter

from wtforms.widgets import CheckboxInput
from wtforms_sqlalchemy.fields import QuerySelectMultipleField

from indico.util.string import natural_sort_key
from indico.web.forms.widgets import JinjaWidget


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
    """Like the parent, but with a callback that allows you to modify the list.

    The callback can return a new list or yield items, and you can use it e.g. to sort the list.
    """

    def __init__(self, *args, modify_object_list=None, collection_class=list, **kwargs):
        self.modify_object_list = modify_object_list
        self.collection_class = collection_class
        super().__init__(*args, **kwargs)

    def _get_object_list(self):
        object_list = super()._get_object_list()
        if self.modify_object_list:
            object_list = list(self.modify_object_list(object_list))
        return object_list

    def _get_data(self):
        data = super()._get_data()
        return self.collection_class(data)

    data = property(_get_data, QuerySelectMultipleField._set_data)


class IndicoQuerySelectMultipleCheckboxField(IndicoQuerySelectMultipleField):
    option_widget = CheckboxInput()
    widget = JinjaWidget('forms/checkbox_group_widget.html', single_kwargs=True)


class IndicoQuerySelectMultipleTagField(IndicoQuerySelectMultipleField):
    widget = JinjaWidget('forms/multiple_tag_select_widget.html', single_kwargs=True, single_line=True)

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            collection_class=set,
            modify_object_list=lambda objs: sorted(objs, key=lambda x: natural_sort_key(x[1].title)),
            get_label=attrgetter('title', 'color'),
            query_factory=self._get_query,
            **kwargs,
        )

    def _get_query(self):
        from indico.modules.events.registration.models.tags import RegistrationTag
        return RegistrationTag.query.with_parent(self.get_form().event)

    @property
    def initial_selection(self):
        return [val for val, __, selected, *__ in self.iter_choices() if selected]

    @property
    def choices(self):
        return [[val, [title, color]] for val, [title, color], *__ in self.iter_choices()]
