# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.requests.controllers import (RHRequestsEventRequestDetails, RHRequestsEventRequestProcess,
                                                        RHRequestsEventRequests, RHRequestsEventRequestWithdraw)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('requests', __name__, template_folder='templates', virtual_template_folder='events/requests',
                      url_prefix='/event/<confId>/manage/requests')

# Event management
_bp.add_url_rule('/', 'event_requests', RHRequestsEventRequests)
_bp.add_url_rule('/<type>/', 'event_requests_details', RHRequestsEventRequestDetails, methods=('GET', 'POST'))
_bp.add_url_rule('/<type>/withdraw', 'event_requests_withdraw', RHRequestsEventRequestWithdraw, methods=('POST',))
_bp.add_url_rule('/<type>/process', 'event_requests_process', RHRequestsEventRequestProcess, methods=('POST',))
