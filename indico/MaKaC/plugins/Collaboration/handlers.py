# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Request handlers for Collaboration plugins
"""

# standard lib imports
import os

# legacy indico imports
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

# indico api imports
from indico.web.rh import RHHtdocs


# Request Handlers

class RHCollaborationHtdocs(RHHtdocs):
    """
    Static file handler for Collaboration plugin
    """

    _url = r"^/Collaboration/(?P<plugin>.*)/(?P<filepath>.*)$"

    @classmethod
    def calculatePath(cls, plugin, filepath):
        module = CollaborationTools.getModule(plugin)

        if module:
            return os.path.join(module.__path__[0],
                                'htdocs', filepath)
        else:
            return None
