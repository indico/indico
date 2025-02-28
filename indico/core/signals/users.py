# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


registered = _signals.signal('registered', '''
Called once a user registers (either locally or joins through a provider). The
*sender* is the new user object.  The kwarg `from_moderation` indicates whether
the user went through a moderation process (this also includes users created
by an administrator manually) or was created immediately on registration;
the identity associated with the registration is passed in the `identity` kwarg.
''')

logged_in = _signals.signal('logged-in', '''
Called when a user logs in. The *sender* is the User who logged in. Depending
on whether this was a regular login or an admin impersonating the user, either
the *identity* kwarg is set to the `Identity` used by the user to log in or the
*admin_impersonation* kwarg is ``True``.
''')

registration_requested = _signals.signal('registration-requested', '''
Called when a user requests to register a new indico account, i.e. if
moderation is enabled.  The *sender* is the registration request.
''')

merged = _signals.signal('merged', '''
Called when two users are merged. The *sender* is the main user while the merged
user (i.e. the one being deleted in the merge) is passed via the *source* kwarg.
''')

db_deleted = _signals.signal('db-deleted', '''
Called when a user is being permanently deleted from the DB. The *sender* is the user
object. Since permanent deletions of users can easily fail due to DB constraints, this
signal is called once BEFORE the deletion actually happens, and then once again after
flushing the changes to the database was successful. Each call contains the `flushed`
kwarg indicating whether the deletion has already been flushed to the database or not.
When using this signal to remove any external data, you must only perform these changes
once the deletion was successful, since otherwise you removed data for a user that still
exists in Indico.
''')

anonymized = _signals.signal('anonymized', '''
Called when a user is being anonymized. The *sender* is the user object.
This signal is called once before the anonymization itself actually happens in case the
code handling the signal needs to access e.g. the email address of the user and once after
the changes have been flushed to the database. Each call contains the `flushed` kwarg
indicating whether the signal is being called before or after flushing the changes.
''')

email_added = _signals.signal('email-added', '''
Called when a new email address is added to a user.  The *sender* is
the user object and the email address is passed in the `email` kwarg.
The `silent` kwarg indicates whether the email was added during some
automated process where no messages should be flashed (e.g. because the sync
was in a background task or triggered during a request from another user).
''')

preferences = _signals.signal('preferences', '''
Expected to return a `ExtraUserPreferences` subclass which implements extra
preferences for the user preference page. The *sender* is the user for whom the
preferences page is being shown which might not be the currently logged-in
user!
''')

primary_email_changed = _signals.signal('primary-email-changed', '''
Called when the primary address is changed. The *sender* is
the user object and the `new` and `old` values are passed as kwargs.
''')

favorite_event_added = _signals.signal('favorite-event-added', '''
Called when a new event is added to a user's favorites. The *sender* is
the user object and the event is passed in the `event` kwarg.
''')

favorite_event_removed = _signals.signal('favorite-event-removed', '''
Called when a new event is removed from a user's favorites. The *sender* is
the user object and the event is passed in the `event` kwarg.
''')

favorite_category_added = _signals.signal('favorite-category-added', '''
Called when a new category is added to a user's favorites. The *sender* is
the user object and the category is passed in the `category` kwarg.
''')

favorite_category_removed = _signals.signal('favorite-category-removed', '''
Called when a new category is removed from a user's favorites. The *sender* is
the user object and the category is passed in the `category` kwarg.
''')

check_login_data = _signals.signal('check-login-data', '''
Called when logging in using a form-based login provider.
The *sender* is the flask-multipass auth provider class used for the login, and
the data entered in the login form is passed in the `data` kwarg. The provider
instance is passed in the `provider` kwarg.
If this signal returns a string, the login will fail with the returned message;
otherwise (``None`` return value) the signup can continue as normal.
''')

check_signup_email = _signals.signal('check-signup-email', '''
Called during the email validation phase of the local account signup process.
The *sender* is the email address the user is trying to use. If this signal returns
a string, the signup will be refused with the returned message; otherwise (``None``
return value) the signup can continue as normal.
''')
