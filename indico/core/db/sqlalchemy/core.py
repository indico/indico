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
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import

import logging

import flask.ext.sqlalchemy
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.utils import cached_property

from zope.sqlalchemy import ZopeTransactionExtension
from .util import IndicoModel

# Monkeypatching this since Flask-SQLAlchemy doesn't let us override the model class
flask.ext.sqlalchemy.Model = IndicoModel


class IndicoSQLAlchemy(SQLAlchemy):
    @cached_property
    def logger(self):
        from indico.core.logger import Logger

        logger = Logger.get('db')
        logger.setLevel(logging.DEBUG)
        return logger


def on_models_committed(sender, changes):
    for obj, change in changes:
        obj.__committed__(change)


db = IndicoSQLAlchemy(session_options={'extension': ZopeTransactionExtension()})
