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


class CaptchaField(fields.String):
    """Validates an answer to a CAPTCHA."""

    def __init__(self):
        def validate(user_answer):
            if plugin := get_captcha_plugin():
                if not plugin.validate_captcha(user_answer):
                    raise ValidationError(_('Incorrect answer'))
            else:
                answer = session.get('captcha_state')
                if not answer or answer != user_answer:
                    raise ValidationError(_('Incorrect answer'))

        super().__init__(required=True, validate=validate)


def get_captcha_plugin():
    """Return the available CAPTCHA plugin."""
    plugins = [p for p in plugin_engine.get_active_plugins().values() if isinstance(p, CaptchaPluginMixin)]
    return plugins[0] if plugins else None


def get_captcha_settings():
    """Return CAPTCHA plugin settings."""
    return plugin.get_captcha_settings() if (plugin := get_captcha_plugin()) else None


def invalidate_captcha():
    """Invalidate the current CAPTCHA.

    Call this function after a successful request to a CAPTCHA-protected endpoint.
    """
    session.pop('captcha_state', None)
