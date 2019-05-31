# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.notifications.controllers import RHNotificationsAdmin, RHSendTestMessage
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('notifications', __name__, template_folder='templates', virtual_template_folder='notifications')

# Application endpoints
_bp.add_url_rule('/admin/notifications', 'admin', RHNotificationsAdmin, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/notifications/send-test', 'send_test', RHSendTestMessage, methods=('POST',))
