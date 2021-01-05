# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()


registered = _signals.signal('registered', """
Called once a user registers (either locally or joins through a provider). The
*sender* is the new user object.  The kwarg `from_moderation` indicates whether
the user went through a moderation process (this also includes users created
by an administrator manually) or was created immediately on registration;
the identity associated with the registration is passed in the `identity` kwarg.
""")

logged_in = _signals.signal('logged-in', """
Called when a user logs in. The *sender* is the User who logged in. Depending
on whether this was a regular login or an admin impersonating the user, either
the *identity* kwarg is set to the `Identity` used by the user to log in or the
*admin_impersonation* kwarg is ``True``.
""")

registration_requested = _signals.signal('registration-requested', """
Called when a user requests to register a new indico account, i.e. if
moderation is enabled.  The *sender* is the registration request.
""")

merged = _signals.signal('merged', """
Called when two users are merged. The *sender* is the main user while the merged
user (i.e. the one being deleted in the merge) is passed via the *source* kwarg.
""")

email_added = _signals.signal('email-added', """
Called when a new email address is added to a user.  The *sender* is
the user object and the email address is passed in the `email` kwarg.
""")

preferences = _signals.signal('preferences', """
Expected to return a `ExtraUserPreferences` subclass which implements extra
preferences for the user preference page. The *sender* is the user for whom the
preferences page is being shown which might not be the currently logged-in
user!
""")
