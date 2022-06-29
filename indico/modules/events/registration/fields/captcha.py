# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow import ValidationError, fields, validates_schema

from indico.core.marshmallow import mm
from indico.modules.events.registration.models.captcha import Captcha
from indico.util.i18n import _
from indico.util.marshmallow import not_empty


class CaptchaField(mm.Schema):
    id = fields.Integer(required=True)
    answer = fields.String(required=True, validate=not_empty)

    @validates_schema(skip_on_field_errors=True)
    def _validate_correct_answer(self, data, **kwargs):
        captcha = Captcha.get(data['id'])

        if not captcha or captcha.is_expired:
            raise ValidationError(_('CAPTCHA is expired, please reload it'))
        elif captcha.answer != data['answer']:
            raise ValidationError(_('Incorrect answer'))
