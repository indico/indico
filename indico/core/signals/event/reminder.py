# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


before_reminder_make_email = _signals.signal('before-reminder-make-email', '''
Executed before a reminder email is created. The `EventReminder` object is the sender.
The parameters to create an email (`to_list`, `from_address`, `template` and `attachments`)
are passed as kwargs; the signal can return a dict used to update the params which will then
be passed to the `make_email` call.
''')
