# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import uuid

from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii


class EventLabel(object):
    # TODO: convert this to a proper model in 2.3
    id = None
    title = None
    color = None

    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            self.id = str(uuid.uuid4())
        for name, value in kwargs.iteritems():
            setattr(self, name, value)

    def __eq__(self, other):
        return isinstance(other, EventLabel) and other.id == self.id

    @locator_property
    def locator(self):
        return {'event_label_id': self.id}

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', _text=self.title)
