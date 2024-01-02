# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


process_args = _signals.signal('process-args', '''
Executed right after `_process_args` of an `RH` instance has been called.
The *sender* is the RH class, the current instance is passed in *rh*.
The return value of `_process_args` (usually ``None``) is available in
*result*.
''')

before_check_access = _signals.signal('before-check-access', '''
Executed right before `_check_access` of an `RH` instance is called.
The *sender* is the RH class, the current instance is passed in *rh*.
If the signal returns ``True`` or ``False``, the original `_check_access` method
will not be executed.  If multiple subscribers to the signal return
contradictory results, ``False`` wins and access is denied.
In case access is denied, a generic error message will be displayed.
For custom errors, raise `Forbidden` yourself while handling the signal.
''')

check_access = _signals.signal('check-access', '''
Executed right after the access check of an `RH` instance has been performed
unless the access check raised an exception.  The *sender* is the RH class,
the current instance is passed in *rh*.
''')

before_process = _signals.signal('before-process', '''
Executed right before `_process` of an `RH` instance is called.
The *sender* is the RH class, the current instance is passed in *rh*.
If a signal handler returns a value, the original `_process` method
will not be executed.  If multiple signal handlers return a value, an
exception is raised.
''')

process = _signals.signal('process', '''
Executed right after `_process` of an `RH` instance has been called.
The *sender* is the RH class, the current instance is passed in *rh*.
The return value of `_process` is available in *result* and if a signal
handler returns a value, it will replace the original return value.
If multiple signals handlers return a value, an exception is raised.
''')
