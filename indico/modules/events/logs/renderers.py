# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
        """Renders the log entry row

        :param entry: A :class:`.EventLogEntry`
        """
        template = '{}:{}'.format(cls.plugin.name, cls.template_name) if cls.plugin is not None else cls.template_name
        return render_template(template, entry=entry, data=cls.get_data(entry), **cls.template_kwargs)

    @classmethod
    def get_data(cls, entry):
        """Returns the entry data in a format suitable for the template.

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
