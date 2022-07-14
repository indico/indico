# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

class CaptchaPluginMixin:
    #: the readable name of the CAPTCHA plugin
    friendly_name = None

    def generate_captcha(self):
        """Returns a CAPTCHA and the correct answer.

        Specifically, the return value is a tuple of `answer, data` where
        `answer` is a string representing the correct answer and `data` is a
        JSON-serializable object holding information needed to render the
        CAPTCHA on the client-side.
        As an example, the built-in CAPTCHA generator
        returns a dictionary with a base64 encoded image and audio data.
        For reCAPTCHA, the `answer` may be `None` as the validation is done externally and
        the `data` will contain the Site key needed to render the reCAPTCHA widget.
        """
        raise NotImplementedError('CAPTCHA plugin must implement generate_captcha()')

    def validate_captcha(self, answer):
        """Validates the answer to a CAPTCHA.

        This should return True when the answer is correct and False otherwise.
        The built-in CAPTCHA simply compares the user-provided with the answer
        stored in the session. Other implementations might need to send a request to
        an external service instead e.g. with reCAPTCHA.
        """
        raise NotImplementedError('CAPTCHA plugin must implement validate_captcha(answer)')
