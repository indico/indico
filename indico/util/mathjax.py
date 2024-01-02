# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import current_app


class MathjaxMixin:
    def _get_head_content(self):
        return str(current_app.manifest['mathjax.js'])
