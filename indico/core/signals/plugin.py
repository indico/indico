# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from blinker import Namespace

_signals = Namespace()


cli = _signals.signal('cli', """
Expected to return one or more click commands/groups.
If they use `indico.cli.core.cli_command` / `indico.cli.core.cli_group`
they will be automatically executed within a plugin context and run
within a Flask app context by default.
""")

shell_context = _signals.signal('shell-context', """
Called after adding stuff to the `indico shell` context.
Receives the `add_to_context` and `add_to_context_multi` keyword args
with functions which allow you to add custom items to the context.
""")

get_blueprints = _signals.signal('get-blueprints', """
Expected to return one or more IndicoPluginBlueprint-based blueprints
which will be registered on the application. The Blueprint must be named
either *PLUGINNAME* or *compat_PLUGINNAME*.
""")

inject_css = _signals.signal('inject-css', """
Expected to return a list of CSS URLs which are loaded after all
other CSS. The *sender* is the WP class of the page.
""")

inject_js = _signals.signal('inject-js', """
Expected to return a list of JS URLs which are loaded after all
other JS. The *sender* is the WP class of the page.
""")

template_hook = _signals.signal('template-hook', """
Expected to return a ``(is_markup, priority, value)`` tuple.
The returned value will be inserted at the location where
this signal is triggered; if multiple receivers are connected
to the signal, they will be ordered by priority.
If `is_markup` is True, the value will be wrapped in a `Markup`
object which will cause it to be rendered as HTML.
The *sender* is the name of the actual hook. The keyword arguments
depend on the hook.
""")

get_event_request_definitions = _signals.signal('get-event-request-definitions', """
Expected to return one or more RequestDefinition subclasses.
""")

get_event_themes_files = _signals.signal('get-event-themes-files', """
Expected to return the path of a themes yaml containing event theme
definitions.
""")
