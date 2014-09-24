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

from blinker import Namespace

__all__ = ('cli', 'shell_context', 'get_blueprints', 'inject_css', 'inject_js')

_signals = Namespace()

cli = _signals.signal('cli', """
Called before running the Flask-Script manager of the `indico`
commandline script. *sender* is the Flask-Script manager which
can be used to register additional commands/managers
""")

shell_context = _signals.signal('shell-context', """
Called after adding stuff to the `indico shell` context.
Receives the `add_to_context` keyword argument with a function
which allows you to add custom items to the context.
""")

get_blueprints = _signals.signal('get-blueprints', """
Expected to return IndicoPluginBlueprint-based blueprints
which will be registered on the application. The signal MUST return
a `(plugin, blueprints)` tuple for technical reasons (the application
needs to know from which plugin a blueprint originates). `blueprints`
can be either a single Blueprint or an iterable containing no more
than two blueprints. The Blueprint must be named either *PLUGINNAME*
or *PLUGINNAME_compat*.
""")

inject_css = _signals.signal('inject-css', """
Expected to return a list of CSS URLs which are loaded after all
other CSS. The *sender* is the WP class of the page.
""")

inject_js = _signals.signal('inject-js', """
Expected to return a list of JS URLs which are loaded after all
other JS. The *sender* is the WP class of the page.
""")
