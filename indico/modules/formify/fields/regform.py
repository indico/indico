# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from wtforms_sqlalchemy.fields import QuerySelectField

from indico.modules.formify.models.forms import RegistrationForm
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.forms.widgets import DropdownWidget


class RegformField(QuerySelectField):
    """A field with dynamic fetching to select a registration form."""

    widget = DropdownWidget(allow_by_id=True, search_field='title', label_field='full_title', preload=True,
                            search_method='POST', inline_js=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('allow_blank', True)
        kwargs.setdefault('render_kw', {}).setdefault('placeholder', _('Enter registration form title or #id'))
        kwargs['query_factory'] = self._get_query
        kwargs['get_label'] = lambda r: f'#{r.id}: {r.title}'
        self.ajax_endpoint = kwargs.pop('ajax_endpoint')
        super().__init__(*args, **kwargs)

    @classmethod
    def _serialize_regform(cls, regform):
        return {'id': regform.id, 'friendly_id': regform.id, 'title': regform.title,
                'full_title': f'# {regform.title}: in category: {regform.owner.id}'}

    def _get_query(self):
        return RegistrationForm.query.filter(RegistrationForm.category_id.in_(self.event.category_chain))

    def pre_validate(self, form):
        super().pre_validate(form)

    def _value(self, for_react=False):
        if not self.data:
            return None
        return [self._serialize_regform(self.data)] if for_react else self.data.id

    @property
    def event(self):
        # This cannot be accessed in __init__ since `get_form` is set
        # afterwards (when the field gets bound to its form) so we
        # need to access it through a property instead.
        return self.get_form().event

    @property
    def search_url(self):
        return url_for(self.ajax_endpoint, self.event)
