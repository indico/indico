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

from indico.core import signals
from indico.util.i18n import _
from indico.web.menu import TopMenuItem, TopMenuSection
from indico.web.util import url_for_index


@signals.menu.sections.connect_via('top-menu')
def _topmenu_sections(sender, **kwargs):
    yield TopMenuSection('services', _('Services'), 60)
    yield TopMenuSection('help', _('Help'), -10)  # put the help section always last


@signals.menu.items.connect_via('top-menu')
def _topmenu_items(sender, **kwargs):
    yield TopMenuItem('home', _('Home'), url_for_index(), 100)
