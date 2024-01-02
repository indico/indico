# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re

from marshmallow import ValidationError, fields, validates_schema

from indico.core.marshmallow import mm
from indico.modules.events.models.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.util.i18n import _
from indico.util.marshmallow import PrincipalPermissionList, not_empty


class ValidRegExField(fields.String):
    """A valid Python regular expression."""

    def _deserialize(self, value, attr, data, **kwargs):
        if len(value) < 2:
            raise ValidationError(_('Empty regex'))
        try:
            return re.compile(value).pattern
        except re.error as exc:
            raise ValidationError(_('Invalid regex: {}').format(exc))


class AutoLinkerRuleSchema(mm.Schema):
    """A regex -> url with placeholders mapping rule."""

    regex = ValidRegExField()
    url = fields.URL(validate=not_empty)

    @validates_schema(skip_on_field_errors=True)
    def _check_url_is_well_formed(self, data, **kwargs):
        regex = data['regex']
        # if de-serialization worked OK, this shouldn't fail
        compiled_regex = re.compile(regex)

        # check that there is at least one group
        if not compiled_regex.groups:
            raise ValidationError(_('The regex needs to have at least one group'))

        # check if all groups are used
        for n in range(1, compiled_regex.groups + 1):
            if f'{{{n}}}' not in data['url']:
                raise ValidationError(_('Not all captured regex groups used ({})').format(n))

        # make sure all groups used exist
        max_placeholder = max(int(m.group(1)) for m in re.finditer(r'\{(\d+)\}', data['url']))
        if max_placeholder > compiled_regex.groups:
            raise ValidationError(_('Placeholder not known: {}').format(max_placeholder))


class EventPermissionsSchema(mm.Schema):
    acl_entries = PrincipalPermissionList(EventPrincipal, all_permissions=True)


class EventDetailsSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        fields = ('id', 'category_chain', 'title', 'start_dt', 'end_dt')

    category_chain = fields.List(fields.String(), attribute='category.chain_titles')


event_permissions_schema = EventPermissionsSchema()
