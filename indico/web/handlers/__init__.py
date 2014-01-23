# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

# system lib imports
import os.path

# legacy imports
from werkzeug.exceptions import NotFound
from indico.core.config import Config


class RH(object):
    pass


class RHHtdocs(RH):

    # the path where source files can be retrieved from
    _local_path = None

    # if available, tells the web app that minimized versions
    # of files may be retrieved from {indico_htdocs}/build/{_min_dir}
    _min_dir = None

    @classmethod
    def calculatePath(cls, filepath, local_path=None, plugin=None):
        config = Config.getInstance()

        # get compiled files from htdocs/build/{_min_dir}
        if '.min.' in filepath and cls._min_dir:
            local_path = os.path.join(config.getHtdocsDir(), 'build', cls._min_dir)
        elif not local_path:
            local_path = cls._local_path

        f_abspath = os.path.abspath(os.path.join(local_path, filepath))
        if f_abspath.startswith(local_path):
            return f_abspath
        raise NotFound
