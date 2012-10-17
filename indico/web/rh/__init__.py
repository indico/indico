# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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


# system lib imports
import os.path

from MaKaC.errors import NotFoundError

from indico.web.wsgi.webinterface_handler_config import SERVER_RETURN, HTTP_NOT_FOUND


class RH(object):
    pass


class RHHtdocs(RH):

    @classmethod
    def calculatePath(cls, filepath):
        f_abspath = os.path.abspath(os.path.join(cls._local_path, filepath))
        if f_abspath.startswith(cls._local_path):
            return f_abspath
        else:
            raise SERVER_RETURN, HTTP_NOT_FOUND
