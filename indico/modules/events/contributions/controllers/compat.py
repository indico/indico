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
