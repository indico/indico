# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
import itertools
import os
import re
import sys
from functools import partial
from operator import itemgetter, attrgetter

import transaction
import sqlalchemy.orm
from flask import current_app
from flask_script import Shell, Option
from werkzeug.local import LocalProxy

import MaKaC
from indico.core import signals
from indico.core.celery import celery
from indico.core.config import Config
from indico.core.db import DBMgr, db
from indico.core.plugins import plugin_engine
from indico.modules.events import Event
from indico.util.console import strip_ansi, cformat
from indico.util.date_time import now_utc, server_to_utc
from indico.util.fossilize import clearCache
from indico.web.flask.util import IndicoConfigWrapper
from MaKaC.common import HelperMaKaCInfo
from MaKaC.conference import Conference, ConferenceHolder


def _add_to_context(namespace, info, element, name=None, doc=None, color='green'):
    if not name:
        name = element.__name__
    namespace[name] = element
    if doc:
        info.append(cformat('+ %%{%s}{}%%{white!} ({})' % color).format(name, doc))
    else:
        info.append(cformat('+ %%{%s}{}' % color).format(name))


def _add_to_context_multi(namespace, info, elements, names=None, doc=None, color='green'):
    if not names:
        names = [x.__name__ for x in elements]
    for name, element in zip(names, elements):
        namespace[name] = element
    if doc:
        info.append(cformat('+ %%{white!}{}:%%{reset} %%{%s}{}' % color).format(doc, ', '.join(names)))
    else:
        info.append(cformat('+ %%{%s}{}' % color).format(', '.join(names)))


def _add_to_context_smart(namespace, info, objects, get_name=attrgetter('__name__'), color='cyan'):
    def _get_module(obj):
        segments = tuple(obj.__module__.split('.'))
        if segments[0].startswith('indico_'):  # plugin
            return 'plugin:{}'.format(segments[0])
        elif segments[:2] == ('indico', 'modules'):
            return 'module:{}'.format(segments[2])
        elif segments[:2] == ('indico', 'core'):
            return 'core:{}'.format(segments[2])
        else:
            return '.'.join(segments[:-1] if len(segments) > 1 else segments)

    items = [(_get_module(obj), get_name(obj), obj) for obj in objects]
    for module, items in itertools.groupby(sorted(items, key=itemgetter(0, 1)), key=itemgetter(0)):
        names, elements = zip(*((x[1], x[2]) for x in items))
        _add_to_context_multi(namespace, info, elements, names, doc=module, color=color)


class IndicoShell(Shell):
    def __init__(self):
        banner = cformat('%{yellow!}Indico v{} is ready for your commands!').format(MaKaC.__version__)
        super(IndicoShell, self).__init__(banner=banner, use_bpython=False)
        self._context = None
        self._info = None

    def __call__(self, app, *args, **kwargs):
        with app.test_request_context(base_url=Config.getInstance().getBaseURL()):
            return self.run(*args, **kwargs)

    def run(self, no_ipython, use_bpython, quiet):
        current_app.config['REPL'] = True  # disables e.g. memoize_request
        context = self.get_context()
        if not quiet:
            self.banner = '\n'.join(self._info + ['', self.banner])
        if use_bpython:
            # bpython does not support escape sequences :(
            # https://github.com/bpython/bpython/issues/396
            self.banner = strip_ansi(self.banner)
        clearCache()
        with context['dbi'].global_connection():
            self.run_shell(no_ipython or use_bpython, not use_bpython, quiet)

    def run_shell(self, no_ipython, no_bpython, quiet):
        # based on the flask-script Shell.run() method
        context = self.get_context()

        if not no_bpython:
            try:
                from bpython import embed
                embed(banner=self.banner, locals_=context)
                return
            except ImportError:
                pass

        if not no_ipython:
            try:
                from IPython.terminal.ipapp import TerminalIPythonApp
                ipython_app = TerminalIPythonApp.instance(user_ns=context, display_banner=not quiet)
                ipython_app.initialize(argv=[])
                ipython_app.shell.show_banner(self.banner)
                ipython_app.start()
                return
            except ImportError:
                pass

        # Use basic python shell
        import code
        code.interact(self.banner, local=context)

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
            add_to_context_multi = partial(_add_to_context_multi, context, self._info)
            add_to_context_smart = partial(_add_to_context_smart, context, self._info)
            # Common stdlib modules
            self._info.append(cformat('*** %{magenta!}stdlib%{reset} ***'))
            DATETIME_ATTRS = ('date', 'time', 'datetime', 'timedelta')
            ORM_ATTRS = ('joinedload', 'defaultload', 'contains_eager', 'lazyload', 'noload', 'subqueryload', 'undefer')
            add_to_context_multi([getattr(datetime, attr) for attr in DATETIME_ATTRS] +
                                 [getattr(sqlalchemy.orm, attr) for attr in ORM_ATTRS] +
                                 [itertools, re, sys, os],
                                 color='yellow')
            # Legacy Indico
            self._info.append(cformat('*** %{magenta!}Legacy%{reset} ***'))
            add_to_context_multi([Conference, ConferenceHolder], color='green')
            add_to_context(LocalProxy(HelperMaKaCInfo.getMaKaCInfoInstance), 'minfo', color='green')
            # Models
            self._info.append(cformat('*** %{magenta!}Models%{reset} ***'))
            models = [cls for name, cls in sorted(db.Model._decl_class_registry.items(), key=itemgetter(0))
                      if hasattr(cls, '__table__')]
            add_to_context_smart(models)
            # Tasks
            self._info.append(cformat('*** %{magenta!}Tasks%{reset} ***'))
            tasks = [task for task in sorted(celery.tasks.values()) if not task.name.startswith('celery.')]
            add_to_context_smart(tasks, get_name=lambda x: x.name.replace('.', '_'), color='blue!')
            # Plugins
            self._info.append(cformat('*** %{magenta!}Plugins%{reset} ***'))
            plugins = [type(plugin) for plugin in sorted(plugin_engine.get_active_plugins().values(),
                                                         key=attrgetter('name'))]
            add_to_context_multi(plugins, color='yellow!')
            # Utils
            self._info.append(cformat('*** %{magenta!}Misc%{reset} ***'))
            add_to_context(celery, 'celery', doc='celery app', color='blue!')
            add_to_context(DBMgr.getInstance(), 'dbi', doc='zodb db interface', color='cyan!')
            add_to_context(db, 'db', doc='sqlalchemy db interface', color='cyan!')
            add_to_context(transaction, doc='transaction module', color='cyan!')
            add_to_context(now_utc, 'now_utc', doc='get current utc time', color='cyan!')
            add_to_context(IndicoConfigWrapper(Config.getInstance()), 'config', doc='indico config')
            add_to_context(current_app, 'app', doc='flask app')
            add_to_context(lambda *a, **kw: server_to_utc(datetime.datetime(*a, **kw)), 'dt',
                           doc='like datetime() but converted from localtime to utc')
            add_to_context(lambda x: ConferenceHolder().getById(x, True), 'E', doc='get event by id (Conference)')
            add_to_context(Event.get, 'EE', doc='get event by id (Event)')
            # Stuff from plugins
            signals.plugin.shell_context.send(add_to_context=add_to_context, add_to_context_multi=add_to_context_multi)

        return self._context
