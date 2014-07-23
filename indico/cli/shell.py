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

import datetime
from flask import current_app
from operator import itemgetter

import transaction
from flask_script import Shell
from werkzeug.local import LocalProxy

import MaKaC
from indico.core.config import Config
from indico.util.console import colored
from indico.core.db import DBMgr, db
from indico.core.index import Catalog
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import Conference, ConferenceHolder, CategoryManager
from MaKaC.plugins import PluginsHolder
from MaKaC.user import AvatarHolder, GroupHolder
from indico.web.flask.util import IndicoConfigWrapper


def _add_to_context(namespace, element, name=None, doc=None, color='green'):
    if not name:
        name = element.__name__
    namespace[name] = element

    if doc:
        print colored('+ {0} : {1}'.format(name, doc), color)
    else:
        print colored('+ {0}'.format(name), color)


class IndicoShell(Shell):
    def __init__(self):
        banner = colored('\nIndico v{} is ready for your commands!\n'.format(MaKaC.__version__),
                         'yellow', attrs=['bold'])
        super(IndicoShell, self).__init__(banner=banner, use_bpython=False)
        self._context = None

    def run(self, **kwargs):
        context = self.get_context()
        with context['dbi'].global_connection():
            super(IndicoShell, self).run(**kwargs)

    def get_context(self):
        if self._context is None:
            self._context = context = {'dbi': DBMgr.getInstance(),
                                       'db': db,
                                       'transaction': transaction}

            for attr in ('date', 'time', 'datetime', 'timedelta'):
                _add_to_context(context, getattr(datetime, attr), doc='stdlib datetime.{}'.format(attr), color='yellow')

            _add_to_context(context, Conference)
            _add_to_context(context, ConferenceHolder)
            _add_to_context(context, CategoryManager)
            _add_to_context(context, AvatarHolder)
            _add_to_context(context, GroupHolder)
            _add_to_context(context, PluginsHolder)
            _add_to_context(context, Catalog)
            _add_to_context(context, IndexesHolder)
            _add_to_context(context, IndicoConfigWrapper(Config.getInstance()), 'config')
            _add_to_context(context, LocalProxy(HelperMaKaCInfo.getMaKaCInfoInstance), 'minfo')
            _add_to_context(context, current_app, 'app')

            for name, cls in sorted(db.Model._decl_class_registry.iteritems(), key=itemgetter(0)):
                if hasattr(cls, '__table__'):
                    _add_to_context(context, cls, color='cyan')

        return self._context
