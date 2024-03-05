# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms import Field

from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.widgets import DropdownWidget


class LinkedObjectField(Field):
    widget = DropdownWidget(allow_by_id=True, search_field='title', label_field='full_title', preload=True,
                            inline_js=True)

    def __init__(self, *args, **kwargs):
        self.ajax_endpoint = kwargs.pop('ajax_endpoint')
        super().__init__(*args, **kwargs)

    def _value(self, for_react=False):
        pass

    @property
    def event(self):
        # This cannot be accessed in __init__ since `get_form` is set
        # afterwards (when the field gets bound to its form) so we
        # need to access it through a property instead.
        return self.get_form().event

    @property
    def search_url(self):
        return url_for(self.ajax_endpoint, self.event)


class ContributionField(LinkedObjectField):
    """A field with dynamic fetching to select a contribution that has no reservation yet."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter contribution title or #id'))
        super().__init__(*args, **kwargs)


class SessionBlockField(LinkedObjectField):
    """A field with dynamic fetching to select a session block that has no reservation yet."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter session block title'))
        super().__init__(*args, **kwargs)
