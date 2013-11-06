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

__all__ = ['DBMgr', 'MigratedDB']

import glob
import importlib
import os

from flask.ext.sqlalchemy import SQLAlchemy

from .manager import DBMgr
from .migration import MigratedDB


db = SQLAlchemy()


def load(package):
    for f in glob.glob(os.path.dirname(__file__) + '/{0}/*.py'.format(package)):
        importlib.import_module('.' + os.path.basename(f)[:-3], __package__ + '.' + package)


def load_room_booking():
    load('rb')
