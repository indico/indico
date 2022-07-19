# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


app_created = _signals.signal('app-created', '''
Called when the app has been created. The *sender* is the flask app.
''')

import_tasks = _signals.signal('import-tasks', '''
Called when Celery needs to import all tasks. Use this signal if you
have modules containing task registered using one of the Celery
decorators but don't import them anywhere.  The signal handler should
only ``import`` these modules and do nothing else.
''')

after_process = _signals.signal('after-process', '''
Called after an Indico request has been processed.  This signal should
also be triggered by CLI utilities that result in other signals being
triggered.
''')

after_commit = _signals.signal('after-commit', '''
Called after an SQL transaction has been committed.  Note that the
session is in 'committed' state when this signal is called, so no SQL
can be emitted while this signal is being handled.
''')

get_storage_backends = _signals.signal('get-storage-backends', '''
Expected to return one or more Storage subclasses.
''')

add_form_fields = _signals.signal('add-form-fields', '''
Lets you add extra fields to a form.  The *sender* is the form class
and should always be specified when subscribing to this signal.

The signal handler should return one or more ``'name', Field`` tuples.
Each field will be added to the form as ``ext__<name>`` and is
automatically excluded from the form's `data` property and its
`populate_obj` method.

To actually process the data, you can use e.g. the `form_validated`
signal and then store it in `flask.g` until another signal informs
you that the operation the user was performing has been successful.
''')

form_validated = _signals.signal('form-validated', '''
Triggered when an IndicoForm was validated successfully.  The *sender*
is the form object.

This signal may return ``False`` to mark the form as invalid even
though WTForms validation was successful.  In this case it is highly
recommended to mark a field as erroneous or indicate the error in some
other way.
''')

get_placeholders = _signals.signal('get-placeholders', '''
Expected to return one or more `Placeholder` objects.
The *sender* is a string (or some other object) identifying the
context.  The additional kwargs passed to this signal depend on
the context.
''')

get_conditions = _signals.signal('get-conditions', '''
Expected to return one or more classes inheriting from `Condition`.
The *sender* is a string (or some other object) identifying the
context.  The additional kwargs passed to this signal depend on
the context.
''')

get_fields = _signals.signal('get-fields', '''
Expected to return field classes.  The *sender* is an object
(or just a string) identifying for what to get fields.  This signal
should never be registered without restricting the sender to ensure
only the correct field types are returned.
''')

db_schema_created = _signals.signal('db-schema-created', '''
Executed when a new database schema is created.  The *sender* is the
name of the schema.
''')

db_query = _signals.signal('db-query', '''
Expected to return exactly one single `Query` object.  The *sender* is a string
identifying the context.  The *query* kwarg contains the query object to be
customized.  The additional kwargs passed to this signal depend on the context.
''')

check_password_secure = _signals.signal('check-password-secure', '''
Check whether a password is secure. The *sender* is a string indicating
the context where the password check happens, the plaintext password is
sent in the *password* kwarg. To fail the security check for a password,
the signal handler should return a string describing why the password is
not secure.
''')

before_notification_send = _signals.signal('before-notification-send', '''
Executed before a notification is sent.  The *sender* is a string representing
the type of notification.  The notification email that will be sent is passed in
the ``email`` kwarg.  The additional kwargs passed to this signal depend on the
context.
''')

get_search_providers = _signals.signal('get-search-providers', '''
Expected to return exactly one `IndicoSearchProvider` subclass. No more than one
handler for this signal may return one as using multiple search providers at the
same time is not possible.
''')
