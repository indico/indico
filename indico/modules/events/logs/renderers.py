# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import render_template

from indico.modules.events.logs.util import render_changes


class EventLogRendererBase(object):
    """Base class for event log renderers."""

    #: unique name of the log renderer (matches EventLogEntry.type)
    name = None
    #: plugin containing this renderer - assigned automatically
    plugin = None
    #: template used to render the log entry
    template_name = None
    #: extra kwargs passed to `render_template`
    template_kwargs = {}

    @classmethod
    def render_entry(cls, entry):
        """Render the log entry row.

        :param entry: A :class:`.EventLogEntry`
        """
        template = '{}:{}'.format(cls.plugin.name, cls.template_name) if cls.plugin is not None else cls.template_name
        return render_template(template, entry=entry, data=cls.get_data(entry), **cls.template_kwargs)

    @classmethod
    def get_data(cls, entry):
        """Return the entry data in a format suitable for the template.

        This method may be overridden if the entry's data needs to be
        preprocessed before being passed to the template.

        It MUST NOT modify `entry.data` directly.
        """
        return entry.data


class SimpleRenderer(EventLogRendererBase):
    name = 'simple'
    template_name = 'events/logs/entry_simple.html'
    template_kwargs = {'compare': render_changes}

    @classmethod
    def get_data(cls, entry):
        data = entry.data
        if isinstance(entry.data, dict):
            data = sorted(entry.data.items())
        return data


class EmailRenderer(EventLogRendererBase):
    name = 'email'
    template_name = 'events/logs/entry_email.html'
