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

from __future__ import unicode_literals

from celery.bin.celery import CeleryCommand
from flask_script import Command

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import update_session_options
from indico.core.celery import celery


class IndicoCeleryCommand(Command):
    """Runs the celery commands within the indico environment"""

    capture_all_args = True
    help_args = ()

    def __call__(self, app=None, *args, **kwargs):
        # We don't need no request context here.
        return self.run(*args, **kwargs)

    def run(self, args):
        update_session_options(db)  # disable the zodb commit hook
        CeleryCommand(celery).execute_from_commandline(['indico celery'] + args)
