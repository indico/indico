# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import current_app, redirect

from indico.modules.events.layout.models.legacy_mapping import LegacyImageMapping, LegacyPageMapping
from indico.web.flask.util import url_for
from indico.web.rh import RHSimple


@RHSimple.wrap_function
def compat_page(**kwargs):
    page = LegacyPageMapping.query.filter_by(**kwargs).first_or_404().page
    return redirect(url_for('event_pages.page_display', page), 302 if current_app.debug else 301)


@RHSimple.wrap_function
def compat_image(**kwargs):
    kwargs.pop('image_ext', None)
    image = LegacyImageMapping.query.filter_by(**kwargs).first_or_404().image
    return redirect(url_for('event_images.image_display', image), 302 if current_app.debug else 301)
