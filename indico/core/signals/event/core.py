# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.signals.event import _signals


sidemenu = _signals.signal('sidemenu', """
Expected to return ``MenuEntryData`` objects to be added to the event side menu.
A single entry can be returned directly, multiple entries must be yielded.
""")

deleted = _signals.signal('deleted', """
Called when an event is deleted. The *sender* is the event object.
The `user` kwarg contains the user performing the deletion if available.
""")

updated = _signals.signal('updated', """
Called when basic data of an event is updated. The *sender* is the event.
A dict of changes is passed in the `changes` kwarg, with ``(old, new)``
tuples for each change. Note than the `person_links` change may happen
with `old` and `new` being the same lists for technical reasons. If the
key is present, it should be assumed that something changed (usually
the order or some data on the person link).
""")

cloned = _signals.signal('cloned', """
Called when an event is cloned. The *sender* is the `Event` object of
the old event, the new event is passed in the `new_event` kwarg.
""")

imported = _signals.signal('imported', """
Called when data is imported to an event. The *sender* is the `Event`
data was imported into, the source event is passed in the `source_event` kwarg.
""")

type_changed = _signals.signal('type-changed', """
Called when the type of an event is changed. The `sender` is the event,
the old type is passed in the `old_type` kwarg.
""")

moved = _signals.signal('moved', """
Called when an event is moved to a different category. The `sender` is the event,
the old category is in the `old_parent` kwarg.
""")

created = _signals.signal('created', """
Called when a new event is created. The `sender` is the new Event. The `cloning`
kwarg indictates whether the event is a clone.
""")

session_updated = _signals.signal('session-updated', """
Called when a session is updated. The *sender* is the session.
""")

session_deleted = _signals.signal('session-deleted', """
Called when a session is deleted. The *sender* is the session.
""")

session_block_deleted = _signals.signal('session-block-deleted', """
Called when a session block is deleted. The *sender* is the session block.
This signal is called before the ``db.session.delete()`` on the block is
executed.
""")

timetable_buttons = _signals.signal('timetable-buttons', """
Expected to return a list of tuples ('button_name', 'js-call-class').
Called when building the timetable view.
""")

get_log_renderers = _signals.signal('get-log-renderers', """
Expected to return `EventLogRenderer` classes.
""")

get_feature_definitions = _signals.signal('get-feature-definitions', """
Expected to return `EventFeature` subclasses.
""")

metadata_postprocess = _signals.signal('metadata-postprocess', """
Called right after a dict-like representation of an event is created,
so that plugins can add their own fields.

The *sender* is a string parameter specifying the source of the metadata.
The *event* kwarg contains the event object. The metadata is passed in
the `data` kwarg. The `user` kwarg contains the user for whom the data is
generated.

The signal should return a dict that will be used to update the
original representation (fields to add or override).
""")
