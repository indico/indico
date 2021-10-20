# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


from indico.modules.events.management.controllers.base import RHManageEventBase
from indico.modules.events.management.views import WPEventPrivacy


class RHEventPrivacy(RHManageEventBase):
    """Show event privacy dashboard."""

    def _process(self):
        return WPEventPrivacy.render_template('privacy_dashboard.html', self.event, 'privacy')
