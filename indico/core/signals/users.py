# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from blinker import Namespace

_signals = Namespace()


registered = _signals.signal('registered', """
Called once a user registers (either locally or joins through a provider). The
*sender* is the new user object.  The kwarg `from_moderation` indicates whether
the user went through a moderation process (this also includes users created
by an administrator manually) or was created immediately on registration;
the identity associated with the registration is passed in the `identity` kwarg.
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
