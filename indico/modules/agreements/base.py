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
from flask_pluginengine import current_plugin, render_plugin_template


class AgreementDefinitionBase(object):
    """AgreementDefinition base class"""

    #: unique name of the agreement definition
    name = None

    #: readable name of the agreement definition
    title = None

    @classmethod
    def render_form(cls, agreement):
        func = render_plugin_template if current_plugin else render_template
        return func('agreements/{}.html'.format(cls.name))

    @staticmethod
    def handle_accepted(agreement):
        """Handles logic on agreement accepted"""
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def handle_rejected(agreement):
        """Handles logic on agreement rejected"""
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def get_people(event):
        """Return the list of people who should receive the agreement"""
        raise NotImplementedError  # pragma: no cover
