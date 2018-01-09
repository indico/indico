# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from blinker import Namespace


_signals = Namespace()


app_created = _signals.signal('app-created', """
Called when the app has been created. The *sender* is the flask app.
""")

import_tasks = _signals.signal('import-tasks', """
Called when Celery needs to import all tasks. Use this signal if you
have modules containing task registered using one of the Celery
decorators but don't import them anywhere.  The signal handler should
only ``import`` these modules and do nothing else.
""")

after_process = _signals.signal('after-process', """
Called after an Indico request has been processed.
""")

get_storage_backends = _signals.signal('get-storage-backends', """
Expected to return one or more Storage subclasses.
""")

add_form_fields = _signals.signal('add-form-fields', """
Lets you add extra fields to a form.  The *sender* is the form class
and should always be specified when subscribing to this signal.

The signal handler should return one or more ``'name', Field`` tuples.
Each field will be added to the form as ``ext__<name>`` and is
automatically excluded from the form's `data` property and its
`populate_obj` method.

To actually process the data, you can use e.g. the `form_validated`
signal and then store it in `flask.g` until another signal informs
you that the operation the user was performing has been successful.
""")

form_validated = _signals.signal('form-validated', """
Triggered when an IndicoForm was validated successfully.  The *sender*
is the form object.

This signal may return ``False`` to mark the form as invalid even
though WTForms validation was successful.  In this case it is highly
recommended to mark a field as erroneous or indicate the error in some
other way.
""")

model_committed = _signals.signal('model-committed', """
Triggered when an IndicoModel class was committed.  The *sender* is
the model class, the model instance is passed as `obj` and the
change type as a string (delete/insert/update) in the `change` kwarg.
""")

get_placeholders = _signals.signal('get-placeholders', """
Expected to return one or more `Placeholder` objects.
The *sender* is a string (or some other object) identifying the
context.  The additional kwargs passed to this signal depend on
the context.
""")

get_conditions = _signals.signal('get-conditions', """
Expected to return one or more classes inheriting from `Condition`.
The *sender* is a string (or some other object) identifying the
context.  The additional kwargs passed to this signal depend on
the context.
""")

get_fields = _signals.signal('get-fields', """
Expected to return `BaseField` subclasses.  The *sender* is an object
(or just a string) identifying for what to get fields.  This signal
should never be registered without restricting the sender to ensure
only the correct field types are returned.
""")

db_schema_created = _signals.signal('db-schema-created', """
Executed when a new database schema is created.  The *sender* is the
name of the schema.
""")
