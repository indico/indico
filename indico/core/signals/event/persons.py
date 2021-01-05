# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.signals.event import _signals


person_updated = _signals.signal('person-updated', """
Called when an EventPerson is modified. The *sender* is the EventPerson.
""")
