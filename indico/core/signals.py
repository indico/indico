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

indico_help = _signals.signal('indico-help', """
Expected to return a dict containing entries for the *Indico help* page::

    entries = {
        _('Section title'): {
            _('Item title'): ('ihelp/.../item.html', 'ihelp/.../item.pdf'),
            _('Item title 2'): ('ihelp/.../item2.html', 'ihelp/.../item2.pdf')
        }
    }
""")

user_preferences = _signals.signal('user-preferences', """
Expected to return/yield one or more ``(title, content)`` tuples which are
shown on the "User Preferences" page. The *sender* is the user for whom the
preferences page is being shown which might not be the currently logged-in
user!
""")

event_management_sidemenu = _signals.signal('event-management-sidemenu', """
Expected to return `(plugin_menu_item_name, SideMenuItem)` tuples to be added to
the event management side menu. The *sender* is the event object.
""")

event_management_clone = _signals.signal('event-management-clone', """
Expected to return an instance of a ``EventCloner`` subclass implementing
the cloning behavior. The *sender* is the event object.
""")

event_management_url = _signals.signal('event-management-url', """
Expected to return a URL for the event management page of the plugin.
This is used when someone who does not have event management access wants
to go to the event management area. He is then redirected to one of the URLs
returned by plugins, i.e. it is not guaranteed that the user ends up on a
specific plugin's management page. The signal should return None if the current
user (available via ``session.user``) cannot access the management area.
The *sender* is the event object.
""")

event_sidemenu = _signals.signal('event-sidemenu', """
Expected to return ``EventMenuEntry`` objects to be added to the event side menu.
A single entry can be returned directly, multiple entries must be yielded.
""")

event_deleted = _signals.signal('event-deleted', """
Called when an event is deleted. The *sender* is the event object.
""")

event_registrant_changed = _signals.signal('event-registrant-changed', """
Called when an event registrant is added or removed. The `sender` is the event,
and the following kwargs are available:

* `user` - the registrant's :class:`Avatar` (or ``None``)
* `registrant` - the :class:`Registrant`
* `action` - the action, i.e. ``'removed'`` or ``'added'``
""")

event_participant_changed = _signals.signal('event-participant-changed', """
Called when an event participant is added or removed. The `sender` is the event,
and the following kwargs are available:

* `user` - the participant's :class:`Avatar` (or ``None``)
* `participant` - the :class:`Participant`
* `old_status` - the previous participation status
* `action` - the action, i.e. ``'removed'`` or ``'added'``

This signal is only triggered if the participation state actually changed, i.e. he's
considered `added` if he was added/approved by a manager or if he accepted an invitation.
The participant is considered `removed` if he's participating (added by a manager or accepted
an invitation) and he's removed from the event or refuses/rejects participation.
""")

event_data_changed = _signals.signal('event-data-changed', """
Called when the basic data of an event is changed. The `sender` is the event,
and the following kwargs are available:

* `attr` - the changed attribute (`title`, `description`, `dates`, `start_date`, `end_date` or `location`)
* `old` - the old value
* `new` - the new value

If the `dates` changed, both `old` and `new` are ``(start_date, end_date)`` tuples.
If the `location` changed, both `old` and `new` are dicts containing `location`, `address` and `room`.

If your plugin reacts to date changes, always make sure to handle all three types.
Depending on the code performing the change, sometimes separate `start_date` and
`end_date` changes are triggered while in other cases a single `dates` change is
triggered.
""")

material_downloaded = _signals.signal('material-downloaded', """
Notifies a file being downloaded. The *sender* is the event and the downloaded
file is passed in the *resource* kwarg.
""")
