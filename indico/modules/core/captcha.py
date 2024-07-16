# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import base64
import random

from captcha.audio import AudioCaptcha
from captcha.image import ImageCaptcha
from flask import session
from marshmallow import ValidationError, fields
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError as WTFValidationError

from indico.core.plugins import plugin_engine
from indico.modules.core.plugins import CaptchaPluginMixin
from indico.util.i18n import _
from indico.web.forms.widgets import JinjaWidget


def _verify_captcha(user_answer):
    if plugin := get_captcha_plugin():
        if (result := plugin.validate_captcha(user_answer)) is not NotImplemented:
            return result

    # No CAPTCHA plugin or a plugin that wants to use the default validation logic
    answer = session.get('captcha_state')
    # 1 and 7 are too similar and we never use 1 in a challenge
    return bool(answer) and answer == user_answer.replace('1', '7')


def generate_captcha_challenge():
    """Generate 4-digit CAPTCHA as image and audio."""
    # we skip 1 since it's too similar to 7; when verifying we accept both digits
    answer = ''.join(random.choices('023456789', k=4))
    image = ImageCaptcha().generate(answer).read()
    audio = AudioCaptcha().generate(answer)
    return {'image': base64.b64encode(image), 'audio': base64.b64encode(audio)}, answer


class CaptchaField(fields.String):
    """Validate an answer to a CAPTCHA."""

    def __init__(self, *args, **kwargs):
        kwargs['required'] = True  # it makes no sense to have an optional CAPTCHA field
        kwargs['allow_none'] = False
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        user_answer = super()._deserialize(value, attr, data, **kwargs)
        if not _verify_captcha(user_answer):
            raise ValidationError(_('Incorrect answer'))
        return user_answer


class WTFCaptchaField(StringField):
    """WTForms field to show a CAPTCHA."""

    widget = JinjaWidget('forms/captcha_widget.html', single_kwargs=True)

    def __init__(self, label=None, validators=None, *args, **kwargs):
        validators = validators or []
        if not any(isinstance(x, DataRequired) for x in validators):
            validators.append(DataRequired())
        super().__init__(label or _('CAPTCHA'), validators, *args, **kwargs)

    @property
    def captcha_settings(self):
        return get_captcha_settings()

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]
        if not _verify_captcha(self.data or ''):
            raise WTFValidationError(_('Incorrect answer'))


def get_captcha_plugin():
    """Return the available CAPTCHA plugin."""
    plugins = [p for p in plugin_engine.get_active_plugins().values()
               if isinstance(p, CaptchaPluginMixin) and p.is_captcha_available()]
    return plugins[0] if plugins else None


def get_captcha_settings():
    """Return CAPTCHA plugin settings."""
    if plugin := get_captcha_plugin():
        return plugin.get_captcha_settings()
    return {}


def invalidate_captcha():
    """Invalidate the current CAPTCHA.

    Call this function after a successful request to a CAPTCHA-protected endpoint.
    """
    session.pop('captcha_state', None)
