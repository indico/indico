# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session


class CaptchaPluginMixin:
    def is_captcha_available(self):
        """Whether this plugin's CAPTCHA is available.

        In case the plugin requires configuration (e.g. an API key in case of
        a cloud-based CAPTCHA) this should return False so no broken CAPTCHA
        is shown to users.
        """
        return True

    def generate_captcha(self):
        """Return a generated CAPTCHA.

        Specifically, the return value must be a JSON-serializable value
        holding information needed to render the CAPTCHA on the client-side.
        If you need to store the correct answer, you can use `set_captcha_state`
        which saves the answer in the user's session. You can later retrieve it
        with `get_captcha_state`.

        As an example, the built-in CAPTCHA generator returns a dictionary with a
        base64 encoded image and audio data, while a cloud-based CAPTCHA plugin may
        not need this method at all.
        """
        return None

    def validate_captcha(self, answer):
        """Validate the answer to a CAPTCHA.

        This should return True when the answer is correct and False otherwise.
        The built-in CAPTCHA simply compares the user-provided value with the answer
        stored in the session. If you store the answer in a session, you can use
        `get_captcha_state` to retrieve it.

        Other implementations might need to send a request to a cloud-based API to validate
        the CAPTCHA.
        """
        raise NotImplementedError('CAPTCHA plugin must implement validate_captcha(answer)')

    def get_captcha_settings(self):
        """Return CAPTCHA settings.

        Use this method if you need to pass some static data to your CAPTCHA React component.
        The return value must be JSON-serializable. The settings will be passed via as a
        `settings` prop to the component.

        For example, a cloud-based CAPTCHA plugin can use this to pass the client-side API key
        (but no secrets!) to the React component displaying the CAPTCHA.
        """
        return {}

    def get_captcha_state(self):
        return session.get('captcha_state')

    def set_captcha_state(self, state):
        session['captcha_state'] = state
