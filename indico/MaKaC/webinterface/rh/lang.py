# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import re
from flask import request

import MaKaC.webinterface.rh.base as base
from indico.core.config import Config

class RHChangeLang(base.RH):

    def _checkParams_POST(self):
        self._language = request.form['lang']

    def _process(self):

        if self._getUser():
            self._getUser().setLang(self._language)

        # No need to do any more processing here. The language change is processed in RH base
        # Remove lang param from referer
        referer = request.referrer or Config.getInstance().getBaseURL()
        referer = re.sub(r'(?<=[&?])lang=[^&]*&?', '', referer)
        referer = re.sub(r'[?&]$', '', referer)
        self._redirect(referer)
