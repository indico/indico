# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.views import WPRoomBookingBase


class RHRoomBooking(RHRoomBookingBase):
    def _process(self):
        return WPRoomBookingBase.display('room_booking.html')
