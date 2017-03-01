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

from __future__ import unicode_literals

from flask import current_app, redirect

from indico.modules.events.layout.models.legacy_mapping import LegacyPageMapping, LegacyImageMapping
from indico.web.flask.util import url_for
from indico.legacy.webinterface.rh.base import RHSimple


@RHSimple.wrap_function
def compat_page(**kwargs):
    page = LegacyPageMapping.find(**kwargs).first_or_404().page
    return redirect(url_for('event_pages.page_display', page), 302 if current_app.debug else 301)


@RHSimple.wrap_function
def compat_image(**kwargs):
    kwargs.pop('image_ext', None)
    image = LegacyImageMapping.find(**kwargs).first_or_404().image
    return redirect(url_for('event_images.image_display', image), 302 if current_app.debug else 301)
