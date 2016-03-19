# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask import request, session, redirect

from MaKaC.webinterface.rh.base import RH


class RHChangeLang(RH):
    def _process(self):
        language = request.form['lang']
        session.lang = language
        if session.user:
            session.user.settings.set('lang', language)

        assert '://' not in request.form['next']  # avoid redirecting to external url
        return redirect(request.form['next'])
