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

from werkzeug.exceptions import Forbidden

from indico.modules.events.layout.util import is_menu_entry_enabled
from indico.util.i18n import _
from MaKaC.errors import MaKaCError
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.pages import authors
from MaKaC.webinterface.rh.contribDisplay import RHContributionDisplayBase


class RHAuthorDisplayBase( RHContributionDisplayBase ):

    def _checkParams( self, params ):
        RHContributionDisplayBase._checkParams( self, params )
        self._authorId = params.get( "authorId", "" ).strip()
        if self._authorId == "":
            raise MaKaCError(_("Author ID not found. The URL you are trying to access might be wrong."))

    def _checkProtection(self):
        RHContributionDisplayBase._checkProtection(self)
        if not is_menu_entry_enabled('author_index', self._conf):
            raise Forbidden()


class RHAuthorDisplay( RHAuthorDisplayBase ):
    _uh = urlHandlers.UHContribAuthorDisplay

    def _process( self ):
        p = authors.WPAuthorDisplay( self, self._contrib, self._authorId )
        return p.display()
