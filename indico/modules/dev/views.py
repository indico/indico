# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.web.views import WPDecorated, WPJinjaMixin


class WPDev(WPJinjaMixin, WPDecorated):
    template_prefix = 'dev/'
    bundles = ('module_dev.js', 'module_dev.css')
    title = 'React Dev'

    def _get_body(self, params):
        return self._get_page_content(params)
