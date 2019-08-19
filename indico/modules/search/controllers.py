# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.search.views import WPSearch
from indico.web.rh import RH


class RHSearch(RH):
    def _process(self):
        return WPSearch.render_template('search.html')
