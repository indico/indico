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

from indico.core import signals
from indico.modules.events.requests.util import get_request_definitions
from indico.modules.events.requests.base import RequestDefinitionBase, RequestFormBase
from indico.modules.events.requests.models.requests import Request


__all__ = ('RequestDefinitionBase', 'RequestFormBase')


@signals.app_created.connect
def _check_request_definitions(app, **kwargs):
    # This will raise RuntimeError if the request type names are not unique
    get_request_definitions()


@signals.merge_users.connect
def _merge_users(user, merged, **kwargs):
    new_id = int(user.id)
    old_id = int(merged.id)
    Request.find(created_by_id=old_id).update({'created_by_id': new_id})
    Request.find(processed_by_id=old_id).update({'processed_by_id': new_id})
