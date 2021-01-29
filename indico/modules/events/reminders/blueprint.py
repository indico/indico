# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.reminders.controllers import (RHAddReminder, RHDeleteReminder, RHEditReminder,
                                                         RHListReminders, RHPreviewReminder)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_reminders', __name__, template_folder='templates',
                      virtual_template_folder='events/reminders', url_prefix='/event/<int:event_id>/manage/reminders')

_bp.add_url_rule('/', 'list', RHListReminders)
_bp.add_url_rule('/add', 'add', RHAddReminder, methods=('GET', 'POST'))
_bp.add_url_rule('/preview', 'preview', RHPreviewReminder, methods=('POST',))
_bp.add_url_rule('/<int:reminder_id>/', 'edit', RHEditReminder, methods=('GET', 'POST'))
_bp.add_url_rule('/<int:reminder_id>/delete', 'delete', RHDeleteReminder, methods=('POST',))
