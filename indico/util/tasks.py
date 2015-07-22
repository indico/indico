# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

"""
This module contains very generic Celery tasks which are not specific
to any other module.  Please add tasks in here only if they are generic
enough to be possibly useful somewhere else.  If you need to import
anything from `indico.modules`, your task most likely does not belong
in here but in your module instead.
"""

from __future__ import unicode_literals

import os

from indico.core.celery import celery
from indico.core.logger import Logger
from indico.util.fs import silentremove


@celery.task(name='delete_file')
def delete_file(path):
    """Deletes a file.

    This task is meant to be invoked with a delay, i.e. like this::

        delete_file.apply_async(args=[file_path], countdown=3600)

    :param path: The absolute path to the file.
    """
    if not os.path.isabs(path):
        raise ValueError('Path is not absolute: {}'.format(path))
    Logger.get().info('Deleting {}'.format(path))
    silentremove(path)
