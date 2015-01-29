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

from __future__ import unicode_literals

from indico.web.forms.base import FormDefaults

from flask import render_template


class RequestDefinitionBase(object):
    """Defines a service request which can be sent by event managers."""

    #: the plugin containing this request definition - assigned automatically
    plugin = None
    #: the unique internal name of the request type
    name = None
    #: the title of the request type as shown to users
    title = None
    #: the :class:`IndicoForm` to use for the request form
    form = None

    @classmethod
    def render_form(cls, **kwargs):
        """Renders the request form

        :param kwargs: arguments passed to the template
        """
        core_tpl = 'events/requests/event_request_details.html'
        plugin_tpl = '{}:event_request_details.html'
        if cls.plugin is None:
            return render_template(core_tpl, **kwargs)
        else:
            return render_template((plugin_tpl.format(cls.plugin.name), core_tpl), **kwargs)

    @classmethod
    def create_form(cls, existing_request=None):
        defaults = FormDefaults(existing_request.data if existing_request else None)
        return cls.form(prefix='request-', obj=defaults)
