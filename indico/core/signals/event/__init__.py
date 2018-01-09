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

# isort:skip_file

from blinker import Namespace


_signals = Namespace()

from indico.core.signals.event.abstracts import *
from indico.core.signals.event.contributions import *
from indico.core.signals.event.core import *
from indico.core.signals.event.designer import *
from indico.core.signals.event.notes import *
from indico.core.signals.event.persons import *
from indico.core.signals.event.registration import *
from indico.core.signals.event.timetable import *
