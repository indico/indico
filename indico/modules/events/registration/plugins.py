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
        CAPTCHA on the client-side. As an example, the built-in CAPTCHA generator
        returns a dictionary with a base64 encoded image and audio.
        """
        raise NotImplementedError('CAPTCHA plugin must implement generate_captcha()')
