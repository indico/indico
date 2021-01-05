# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals


class VCRoomError(Exception):
    def __init__(self, message, field=None):
        super(VCRoomError, self).__init__(message)
        self.message = message
        self.field = field


class VCRoomNotFoundError(VCRoomError):
    def __init__(self, message):
        super(VCRoomNotFoundError, self).__init__(message)
