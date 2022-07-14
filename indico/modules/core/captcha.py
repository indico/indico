# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from marshmallow import ValidationError, fields

from indico.core.plugins import plugin_engine
from indico.modules.events.registration.plugins import CaptchaPluginMixin
from indico.util.i18n import _
from indico.util.marshmallow import not_empty


class CaptchaField(fields.String):
    """Validates an answer to a CAPTCHA."""

    def __init__(self):
        super().__init__(required=True, validate=not_empty)

    def _validate(self, user_answer):
        if plugin := get_captcha_plugin():
            if not plugin.validate_captcha(user_answer):
                raise ValidationError(_('Incorrect answer'))
        else:
            super()._validate(user_answer)
            answer = session.get('captcha_answer', None)
            if not answer or answer != user_answer:
                raise ValidationError(_('Incorrect answer'))


def get_captcha_plugin():
    """Return the available CAPTCHA plugin."""

    plugins = [p for p in plugin_engine.get_active_plugins().values() if isinstance(p, CaptchaPluginMixin)]
    return plugins[0] if plugins else None
