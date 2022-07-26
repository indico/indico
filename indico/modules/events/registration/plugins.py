# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session


class CaptchaPluginMixin:
    #: the readable name of the CAPTCHA plugin
    friendly_name = None

    def generate_captcha(self):
        """Return a generated CAPTCHA.

        Specifically, the return value must be a JSON-serializable value
        holding information needed to render the CAPTCHA on the client-side.
        If you need to store the correct answer, you can use `set_captcha_state`
        which saves the answer in the user's session. You can later retrieve it
        with `get_captcha_state`.

        As an example, the built-in CAPTCHA generator
        returns a dictionary with a base64 encoded image and audio data.
        For reCAPTCHA, the `answer` may be `None` as the validation is done externally and
        the `data` will contain the Site key needed to render the reCAPTCHA widget.
        """
        raise NotImplementedError('CAPTCHA plugin must implement generate_captcha()')

    def validate_captcha(self, answer):
        """Validate the answer to a CAPTCHA.

        This should return True when the answer is correct and False otherwise.
        The built-in CAPTCHA simply compares the user-provided value with the answer
        stored in the session. If you store the answer in a session,
        you can use `get_captcha_state` to retrieve it.

        Other implementations might need to send a request to
        an external service instead e.g. with reCAPTCHA.
        """
        raise NotImplementedError('CAPTCHA plugin must implement validate_captcha(answer)')

    def get_captcha_state(self):
        return session.get('captcha_state')

    def set_captcha_state(self, state):
        session['captcha_state'] = state
