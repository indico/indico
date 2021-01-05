# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
