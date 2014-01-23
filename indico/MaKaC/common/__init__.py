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

# We load Configuration from setup.py which in turns loads this (although it
# is not needed). If we still don't have the dependencies installed this will
# crash and that's why we selectively install them or not.
from MaKaC.consoleScripts.installBase import getIndicoInstallMode
skip_imports = getIndicoInstallMode()

if not skip_imports:

    __all__ = ['HelperMaKaCInfo', 'URL', 'Config']

    from .Configuration import Config
    from .info import HelperMaKaCInfo
    from .url import URL
