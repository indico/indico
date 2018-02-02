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

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()


process_args = _signals.signal('process-args', """
Executed right after `_process_args` of an `RH` instance has been called.
The *sender* is the RH class, the current instance is passed in *rh*.
The return value of `_process_args` (usually ``None``) is available in
*result*.
""")

check_access = _signals.signal('check-access', """
Executed right after `_check_access` of an `RH` instance has been called
unless the access check raised an exception.  The *sender* is the RH class,
the current instance is passed in *rh*.
""")

before_process = _signals.signal('before-process', """
Executed right before `_process` of an `RH` instance is called.
The *sender* is the RH class, the current instance is passed in *rh*.
If a signal handler returns a value, the original `_process` method
will not be executed.  If multiple signal handlers return a value, an
exception is raised.
""")

process = _signals.signal('process', """
Executed right after `_process` of an `RH` instance has been called.
The *sender* is the RH class, the current instance is passed in *rh*.
The return value of `_process` is available in *result* and if a signal
handler returns a value, it will replace the original return value.
If multiple signals handlers return a value, an exception is raised.
""")
