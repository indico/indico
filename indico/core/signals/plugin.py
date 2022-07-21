# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


cli = _signals.signal('cli', '''
Expected to return one or more click commands/groups.
If they use `indico.cli.core.cli_command` / `indico.cli.core.cli_group`
they will be automatically executed within a plugin context and run
within a Flask app context by default.
''')

shell_context = _signals.signal('shell-context', '''
Called after adding stuff to the `indico shell` context.
Receives the `add_to_context` and `add_to_context_multi` keyword args
with functions which allow you to add custom items to the context.
''')

get_blueprints = _signals.signal('get-blueprints', '''
Expected to return one or more IndicoPluginBlueprint-based blueprints
which will be registered on the application. The Blueprint must be named
either *PLUGINNAME* or *compat_PLUGINNAME*.
''')

inject_bundle = _signals.signal('inject-bundle', '''
Expected to return a list of bundle names which are loaded after all
the rest. The *sender* is the WP class of the page.
''')

template_hook = _signals.signal('template-hook', '''
Expected to return a ``(is_markup, priority, value)`` tuple.
The returned value will be inserted at the location where
this signal is triggered; if multiple receivers are connected
to the signal, they will be ordered by priority.
If `is_markup` is True, the value will be wrapped in a `Markup`
object which will cause it to be rendered as HTML.
The *sender* is the name of the actual hook. The keyword arguments
depend on the hook.
''')

get_event_request_definitions = _signals.signal('get-event-request-definitions', '''
Expected to return one or more RequestDefinition subclasses.
''')

get_event_themes_files = _signals.signal('get-event-themes-files', '''
Expected to return the path of a themes yaml containing event theme
definitions.
''')

get_conference_themes = _signals.signal('get-conference-themes', '''
Expected to return one or more :class:`indico.modules.events.layout.util.ConferenceTheme`
objects containing the information about custom conference themes.

Required:
- ``name``     -- string indicating the internal name used for the stylesheet which will be
                  stored when the theme is selected in an event.
- ``css_path`` -- string indicating the location of the CSS file, relative to the
                  plugin's ``static`` folder.
- ``title``    -- string indicating the title displayed to the user when selecting the theme.

Optional:
- ``js_path``  -- string indicating the location for a simple, static javascript file to be
                  loaded, relative to the plugin's ``static`` folder.
''')

get_template_customization_paths = _signals.signal('get-template-customization-paths', '''
Expected to return the absolute path to a directory containing template overrides.
This signal is called once during initialization so it should not use any
data that may change at runtime.  The behavior of a customization path returned
by this function is exactly like ``<CUSTOMIZATION_DIR>/templates``, but
it has lower priority than the one from the global customization dir.
''')

schema_post_dump = _signals.signal('schema-post-dump', '''
Called when a marshmallow schema is dumped. The *sender* is the schema class
and code using this signal should always specify it. The signal is called with
the following arguments:

- ``many`` -- bool indicating whether the data was dumped with ``many=True`` or not
- ``data`` -- the dumped data. this is guaranteed to be a list; in case of ``many=False``
              it is guaranteed to contain exactly one element
- ``orig`` -- the original data before dumping. just like ``data`` it is always a list

If a plugin wants to modify the data returned when dumping, it may do so by modifying
the contents of ``data``.
''')

schema_pre_load = _signals.signal('schema-pre-load', '''
Called when a marshmallow schema is loaded. The *sender* is the schema class
and code using this signal should always specify it. The signal is called with
the following arguments:

- ``data`` -- the raw data passed to marshmallow; this is usually a dict of raw
              json/form data coming from the user, so it can have all types valid
              in JSON

If a plugin wants to modify the data the schema will eventually load, it may do so by
modifying the contents of ``data``.
''')

schema_post_load = _signals.signal('schema-post-load', '''
Called after a marshmallow schema is loaded. The *sender* is the schema class
and code using this signal should always specify it. The signal is called with
the following arguments:

- ``data`` -- the data returned by marshmallow; this is usually a dict which may contain
              more complex data types than those valid in JSON

If a plugin wants to modify the resulting data, it may do so by modifying the contents of
``data``.
''')

interceptable_function = _signals.signal('interceptable-function', '''
This signal provides a generic way to let plugins intercept function calls and
inspect or modify their call arguments. The sender should always be taken from the
:func:`~indico.util.signals.interceptable_sender` util and not be used directly.

The signal handler also receives the original function in the ``func`` kwarg and the
:class:`~inspect.BoundArguments` for the original function call in the ``args`` kwarg.
Additional context may be preovided in the ``ctx`` kwargs.

The args object is mutable; its `arguments` attribute is a dict containing all the arguments
of the original function call; if necessary its `apply_defaults` method can be called to
fill in any default values the function provides.

The signal handler may also return a value; if it does so, the original function will NOT
be called but rather the returned value used. Note that using the signal in this way should
only be done if you are very sure that no other signal handler does so, as the function call
will fail with an error in case more than one return value override is specified.

Due to how Python works, returning an explicit ``None`` in order to override the return value
with ``None`` won't work; but you can use the special ``RETURN_NONE`` kwarg for this purpose.

Note that this signal does NOT let you intercept arbitrary functions; only those which are
either decorated or where the caller explicitly wrapped the function using
:func:`~indico.util.signals.make_interceptable` can be intercepted. If you believe a certain
function should allow this, you're welcome to send a Pull Request.
''')
