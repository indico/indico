# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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


access_granted = _signals.signal('access-granted', """
Called when a principal in an `AccessController` is granted access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

access_revoked = _signals.signal('access-revoked', """
Called when a principal in an `AccessController` is revoked access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

modification_granted = _signals.signal('modification-granted', """
Called when a principal in an `AccessController` is granted modification access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

modification_revoked = _signals.signal('modification-revoked', """
Called when a principal in an `AccessController` is revoked modification access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")
