# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import current_app, redirect

from indico.modules.events.contributions.models.legacy_mapping import (LegacyContributionMapping,
                                                                       LegacySubContributionMapping)
from indico.web.flask.util import url_for
from indico.web.rh import RHSimple


@RHSimple.wrap_function
def compat_contribution(_endpoint, event_id, legacy_contribution_id, **kwargs):
    contrib = (LegacyContributionMapping
               .find(event_id=event_id, legacy_contribution_id=legacy_contribution_id)
               .first_or_404()
               .contribution)
    url = url_for('contributions.' + _endpoint, contrib)
    return redirect(url, 302 if current_app.debug else 301)


@RHSimple.wrap_function
def compat_subcontribution(event_id, legacy_contribution_id, legacy_subcontribution_id, **kwargs):
    subcontrib = (LegacySubContributionMapping
                  .find(event_id=event_id, legacy_contribution_id=legacy_contribution_id,
                        legacy_subcontribution_id=legacy_subcontribution_id)
                  .first_or_404()
                  .subcontribution)
    url = url_for('contributions.display_subcontribution', subcontrib)
    return redirect(url, 302 if current_app.debug else 301)
