# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

import MaKaC.plugins.InstantMessaging.rh as handlers
from indico.web.flask.util import rh_as_view, make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


blueprint = IndicoBlueprint('instantmessaging', __name__)

blueprint.add_url_rule('/confModifChat', 'confModifChat', rh_as_view(handlers.RHChatFormModif))
blueprint.add_url_rule('/confModifChat/logs', 'confModifChat-logs', rh_as_view(handlers.RHChatSeeLogs))
blueprint.add_url_rule('/<confId>/chat', 'conferenceInstantMessaging', rh_as_view(handlers.RHInstantMessagingDisplay))

blueprint.add_url_rule('/InstantMessaging/<path:filepath>', 'htdocs', rh_as_view(handlers.RHInstantMessagingHtdocs))

# we can't use make_compat_blueprint here because the old url doesn't end in .py
compat = IndicoBlueprint('compat_instantmessaging', __name__)
compat.add_url_rule('/conferenceInstantMessaging', 'conferenceInstantMessaging',
                    make_compat_redirect_func(blueprint, 'conferenceInstantMessaging'))
