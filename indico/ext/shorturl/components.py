# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

# dependency libs
from zope.interface import implements

# indico imports
from indico.core.extpoint import Component
from indico.core.extpoint.events import IEventDisplayContributor
from indico.ext.shorturl.register import ShortUrlRegister
from indico.ext import shorturl

from indico.ext.shorturl.chrome import WEventDetailBanner


class ShortUrlContributor(Component):
    """
    This component listens for events and directs them to the MPT.
    Implements ``EventDisplayContributor``
    """

    implements(IEventDisplayContributor)

    def eventDetailBanner(self, obj, conf):
        """
        Returns the info that the plugins want to add after the header (where description is)
        """
        vars = {}
        vars["shortUrls"] = [generator.generateShortURL(conf) for generator in ShortUrlRegister().getAllPlugins()]
        return WEventDetailBanner.forModule(shorturl).getHTML(vars)

