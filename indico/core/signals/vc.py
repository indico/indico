# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


new_vc_room = _signals.signal(
    'new-vc-room',
    '''Called whenever a new VC room is created. The *sender* is the new `VCRoom` object.
The `event` kwarg contains the event where the room was created, while `assoc` holds
the actual `VCRoomEventAssociation`.''',
)

deleted_vc_room = _signals.signal(
    'deleted-vc-room',
    '''Called whenever a VC room is deleted, right before the user is notified about the
operation and the object deleted from the DB. The *sender* is the actual `VCRoom`
object, in its most terminal state. An `event` kwarg holds the event the `VCRoom`
used to be in.''',
)

attached_vc_room = _signals.signal(
    'attached-vc-room',
    '''Called whenever a room is attached to a new object (e.g. event, contribution...),
as a consequence of a direct or indirect user action. This triggers on creation of
a `VCRoom`, modification of the object it is linked to, or attachment of an existing
`VCRoom` to an object (e.g. event, contribution...). The *sender* is the
`VCRoomEventAssociation`, followed by the kwargs `vc_room` (the actual `VCRoom` which
is being attached), `event` (event where the operation is being executed), `data` (form
data) and `old_link` (object which the association was pointing to before, if any).
`new_room` is a bool stating whether this is a newly-created room or one changing `link_object`''',
)

detached_vc_room = _signals.signal(
    'detached-vc-room',
    '''Called whenever a room is detached from an object (e.g. event, contribution...),
as a consequence of a direct or indirect user action. This triggers on direct detachment
 of the object a `VCRoomEventAssociation` is linked to. The *sender* is the
`VCRoomEventAssociation`, followed by the kwargs `vc_room` (the actual `VCRoom` which
is being detached), `old_link` (what it is being detached from), `event` (event where the operation
is being executed) and `data` (form data).''',
)

cloned_vc_room = _signals.signal(
    'cloned-vc-room',
    '''Called whenever a `VCRoomEventAssociation` is cloned. The *sender* is the original object,
with the cloned object passed in the `new_assoc` kwarg. The `vc_room` in question is also
passed along, as well as the new `link_object`.''',
)

updated_vc_room_data = _signals.signal(
    'updated-vc-room-data',
    '''Called whenever a `VCRoom`'s data is changed. The *sender* is the `VCRoom` object,
and the `data` arg contains a dictionary of tuples containing the new data.''',
)
