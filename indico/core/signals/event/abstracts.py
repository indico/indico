# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


abstract_created = _signals.signal('abstract-created', """
Called when a new abstract is created. The `sender` is the new abstract.
""")

abstract_deleted = _signals.signal('abstract-deleted', """
Called when an abstract is deleted. The *sender* is the abstract.
""")

abstract_state_changed = _signals.signal('abstract-state-changed', """
Called when an abstract is withdrawn. The *sender* is the abstract.
""")

abstract_updated = _signals.signal('abstract-updated', """
Called when an abstract is modified. The *sender* is the abstract.
""")
