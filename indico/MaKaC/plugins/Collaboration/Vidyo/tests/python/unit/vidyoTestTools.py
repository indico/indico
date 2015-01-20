# -*- coding: utf-8 -*-+
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

from MaKaC.plugins import PluginsHolder
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools

class VidyoTestSetup(object):

    @classmethod
    def setup(cls):

        # lazy import because we don't want it to be imported by default
        # (as the plugin system currently loads all submodules)
        from indico.tests.config import TestConfig

        PluginsHolder().loadAllPlugins()

        testConfig = TestConfig.getInstance()
        vidyoOptions = CollaborationTools.getPlugin("Vidyo").getOptions()

        vidyoOptions["indicoUsername"].setValue(testConfig.getCollaborationOptions()["Vidyo"]["indicoUsername"])
        vidyoOptions["indicoPassword"].setValue(testConfig.getCollaborationOptions()["Vidyo"]["indicoPassword"])

        cls._setupDone = True
