# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


before_reminder_make_email = _signals.signal('before-reminder-make-email', '''
 Executed before reminder email is sent. The `EventReminder` object is the sender.
 The parameters to create an email `to_list`, `from_address`, `template` and `attachments` are passed in the kwargs.
 The signal can modify existing parameters or return a dictionary to add any other parameter to the make_email.
''')
