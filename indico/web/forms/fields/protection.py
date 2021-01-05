# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import absolute_import, unicode_literals

from flask import render_template
from markupsafe import Markup

from indico.core.db import db
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.util.i18n import _
from indico.web.forms.fields import IndicoEnumRadioField
from indico.web.forms.widgets import JinjaWidget


class IndicoProtectionField(IndicoEnumRadioField):
    widget = JinjaWidget('forms/protection_widget.html', single_kwargs=True)
    radio_widget = JinjaWidget('forms/radio_buttons_widget.html', orientation='horizontal', single_kwargs=True)

    def __init__(self, *args, **kwargs):
        self.protected_object = kwargs.pop('protected_object')(kwargs['_form'])
        get_acl_message_url = kwargs.pop('acl_message_url', None)
        self.acl_message_url = get_acl_message_url(kwargs['_form']) if get_acl_message_url else None
        self.can_inherit_protection = self.protected_object.protection_parent is not None
        if not self.can_inherit_protection:
            kwargs['skip'] = {ProtectionMode.inheriting}
        super(IndicoProtectionField, self).__init__(*args, enum=ProtectionMode, **kwargs)

    def render_protection_message(self):
        protected_object = self.get_form().protected_object
        if hasattr(protected_object, 'get_non_inheriting_objects'):
            non_inheriting_objects = protected_object.get_non_inheriting_objects()
        else:
            non_inheriting_objects = []
        if isinstance(protected_object.protection_parent, db.m.Event):
            parent_type = _('Event')
        elif isinstance(protected_object.protection_parent, db.m.Category):
            parent_type = _('Category')
        else:
            parent_type = _('Session')
        rv = render_template('_protection_info.html', field=self, protected_object=protected_object,
                             parent_type=parent_type, non_inheriting_objects=non_inheriting_objects)
        return Markup(rv)
