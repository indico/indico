# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


vc_room_created = _signals.signal('vc-room-created', '''
Called whenever a new VC room is created. The *sender* is the new `VCRoom` object.
The `event` kwarg contains the event where the room was created, while `assoc` holds
the actual `VCRoomEventAssociation`.
''')

vc_room_deleted = _signals.signal('vc-room-deleted', '''
Called whenever a VC room is deleted, right before the user is notified about the
operation and the object deleted from the DB. The *sender* is the actual `VCRoom`
object, in its most terminal state. An `event` kwarg holds the event the `VCRoom`
used to be in.
''')

vc_room_attached = _signals.signal('vc-room-attached', '''
Called whenever a room is attached to a new object (e.g. event, contribution...),
as a consequence of a direct or indirect user action. This triggers on creation of
a `VCRoom`, modification of the object it is linked to, or attachment of an existing
`VCRoom` to an object (e.g. event, contribution...). The *sender* is the
`VCRoomEventAssociation`, followed by the kwargs `vc_room` (the actual `VCRoom` which
is being attached), `event` (event where the operation is being executed), `data` (form
data) and `old_link` (object which the association was pointing to before, if any).
`new_room` is a bool stating whether this is a newly-created room or one changing `link_object`
''')

vc_room_detached = _signals.signal('vc-room-detached', '''
Called whenever a room is detached from an object (e.g. event, contribution...),
as a consequence of a direct or indirect user action. This triggers on direct detachment
of the object a `VCRoomEventAssociation` is linked to. The *sender* is the
`VCRoomEventAssociation`, followed by the kwargs `vc_room` (the actual `VCRoom` which
is being detached), `old_link` (what it is being detached from), `event` (event where the operation
is being executed) and `data` (form data).
''')

vc_room_cloned = _signals.signal('vc-room-cloned', '''
Called whenever a `VCRoomEventAssociation` is cloned. The *sender* is the original object,
with the cloned object passed in the `new_assoc` kwarg. The `vc_room` in question is also
passed along, as well as the new `link_object`.
''')

vc_room_data_updated = _signals.signal('vc-room-data-updated', '''
Called whenever a `VCRoom`'s data is changed. The *sender* is the `VCRoom` object,
and the `data` arg contains a dictionary of tuples containing the new data.
''')
