# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


get_cloners = _signals.signal('get_cloners', """
Expected to return one or more ``EventCloner`` subclasses implementing
a cloning operation for something within an event.
""")

management_url = _signals.signal('management-url', """
Expected to return a URL for the event management page of the plugin.
This is used when someone who does not have event management access wants
to go to the event management area. He is then redirected to one of the URLs
returned by plugins, i.e. it is not guaranteed that the user ends up on a
specific plugin's management page. The signal should return None if the current
user (available via ``session.user``) cannot access the management area.
The *sender* is the event object.
""")

image_created = _signals.signal('image-uploaded', """
Called when a new image is created.  The *sender* object is the new ``ImageFile``.
The user who uploaded the image is passed in the ``user`` kwarg.
""")

image_deleted = _signals.signal('image-deleted', """
Called when an image is deleted.  The *sender* object is the ``ImageFile`` that is
about to be deleted.  The user who uploaded the image is passed in the ``user``
kwarg.
""")
