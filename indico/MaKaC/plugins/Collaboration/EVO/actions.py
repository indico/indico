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

from MaKaC.plugins.base import ActionBase
from MaKaC.plugins.Collaboration.EVO.common import EVOControlledException, getEVOAnswer, EVOException,\
    getEVOOptionValueByName
from MaKaC.i18n import _

pluginActions = [
    ("reloadCommunityList", {"buttonText": "Reload Community List",
                            "associatedOption": "communityList"} )
]

class ReloadCommunityListAction(ActionBase):

    def call(self):

        try:
            answer = getEVOAnswer("reloadCommunityList")
        except EVOControlledException, e:
            raise EVOException('Error when parsing list of communities. Message from EVO Server: "' + e.message + '".')

        try:
            communityStringList = answer.split('&&')
            communities = {}

            ignoredCommunities = getEVOOptionValueByName("ingnoredCommunities")

            for communityString in communityStringList:
                id, name = communityString.split(',')
                id = id.strip()
                name = name.strip()
                if id not in ignoredCommunities:
                    communities[id] = name
            self._plugin.getOption("communityList").setValue(communities)

        except Exception, e:
            raise EVOException('Error when parsing list of communities. Message from EVO Server: "' + answer + '". Exception ocurred: ' + str(e))



