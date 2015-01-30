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

from flask import render_template

from indico.core.plugins import plugin_context


class AgreementDefinitionBase(object):
    """AgreementDefinition base class"""

    #: unique name of the agreement definition
    name = None
    #: readable name of the agreement definition
    title = None
    #: plugin containing this agreement definition - assigned automatically
    plugin = None

    @classmethod
    def render_form(cls, agreement):
        tpl = '{}.html'.format(cls.name)
        core_tpl = 'agreements/{}'.format(tpl)
        plugin_tpl = '{{}}:{}'.format(tpl)
        if cls.plugin is None:
            return render_template(core_tpl)
        else:
            with plugin_context(cls.plugin):
                render_template((plugin_tpl.format(cls.plugin.name), core_tpl))

    @classmethod
    def handle_accepted(cls, agreement):
        """Handles logic on agreement accepted"""
        pass  # pragma: no cover

    @classmethod
    def handle_rejected(cls, agreement):
        """Handles logic on agreement rejected"""
        pass  # pragma: no cover

    @classmethod
    def handle_reset(cls, agreement):
        """Handles logic on agreement reset"""
        pass  # pragma: no cover

    @classmethod
    def get_people(cls, event):
        """Return the list of people who should receive the agreement"""
        raise NotImplementedError  # pragma: no cover
