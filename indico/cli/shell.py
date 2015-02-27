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

import datetime
from functools import partial
from operator import itemgetter

import transaction
from flask import current_app
from flask_script import Shell, Option
from werkzeug.local import LocalProxy

import MaKaC
from indico.core import signals
from indico.core.config import Config
from indico.util.console import colored, strip_ansi
from indico.core.db import DBMgr, db
from indico.core.index import Catalog
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.indexes import IndexesHolder
from MaKaC.conference import Conference, ConferenceHolder, CategoryManager
from MaKaC.user import AvatarHolder, GroupHolder
from indico.web.flask.util import IndicoConfigWrapper


def _add_to_context(namespace, info, element, name=None, doc=None, color='green'):
    if not name:
        name = element.__name__
    namespace[name] = element

    attrs = {}
    if color[-1] == '!':
        color = color[:-1]
        attrs['attrs'] = ['bold']

    if doc:
        info.append(colored('+ {0} : {1}'.format(name, doc), color, **attrs))
    else:
        info.append(colored('+ {0}'.format(name), color, **attrs))


class IndicoShell(Shell):
    def __init__(self):
        banner = colored('\nIndico v{} is ready for your commands!\n'.format(MaKaC.__version__),
                         'yellow', attrs=['bold'])
        super(IndicoShell, self).__init__(banner=banner, use_bpython=False)
        self._context = None
        self._info = None
        self._quiet = False

    def run(self, no_ipython, use_bpython, quiet):
        context = self.get_context()
        if not quiet:
            self.banner = '\n'.join(self._info + [self.banner])
        if use_bpython:
            # bpython does not support escape sequences :(
            # https://github.com/bpython/bpython/issues/396
            self.banner = strip_ansi(self.banner)
        with context['dbi'].global_connection():
            super(IndicoShell, self).run(no_ipython or use_bpython, not use_bpython)

    def get_options(self):
        return (
            Option('--no-ipython', action='store_true', dest='no_ipython', default=False,
                   help="Do not use the IPython shell"),
            Option('--use-bpython', action='store_true', dest='use_bpython', default=False,
                   help="Use the BPython shell"),
            Option('--quiet', '-q', action='store_true', dest='quiet', default=False,
                   help="Do not print the shell context")
        )

    def get_context(self):
        if self._context is None:
            self._context = context = {}
            self._info = []

            add_to_context = partial(_add_to_context, context, self._info)

            for attr in ('date', 'time', 'datetime', 'timedelta'):
                add_to_context(getattr(datetime, attr), doc='stdlib datetime.{}'.format(attr), color='yellow')

            add_to_context(Conference)
            add_to_context(ConferenceHolder)
            add_to_context(CategoryManager)
            add_to_context(AvatarHolder)
            add_to_context(GroupHolder)
            add_to_context(Catalog)
            add_to_context(IndexesHolder)
            add_to_context(IndicoConfigWrapper(Config.getInstance()), 'config')
            add_to_context(LocalProxy(HelperMaKaCInfo.getMaKaCInfoInstance), 'minfo')
            add_to_context(current_app, 'app')

            for name, cls in sorted(db.Model._decl_class_registry.iteritems(), key=itemgetter(0)):
                if hasattr(cls, '__table__'):
                    add_to_context(cls, color='cyan')

            add_to_context(DBMgr.getInstance(), 'dbi', doc='zodb db interface', color='cyan!')
            add_to_context(db, 'db', doc='sqlalchemy db interface', color='cyan!')
            add_to_context(transaction, doc='transaction module', color='cyan!')
            signals.plugin.shell_context.send(add_to_context=add_to_context)

        return self._context
