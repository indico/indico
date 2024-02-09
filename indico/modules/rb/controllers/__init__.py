# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session
from werkzeug.exceptions import Forbidden, NotFound

from indico.core.config import config
from indico.modules.rb import BookingReasonRequiredOptions, rb_settings
from indico.modules.rb.util import rb_check_user_access
from indico.util.i18n import _
from indico.web.rh import RHProtected
from indico.web.util import ExpectedError


class RHRoomBookingBase(RHProtected):
    """Base class for room booking RHs."""

    def _check_access(self):
        if not config.ENABLE_ROOMBOOKING:
            raise NotFound(_('The room booking module is not enabled.'))
        RHProtected._check_access(self)
        if not rb_check_user_access(session.user):
            raise Forbidden(_('You are not authorized to access the room booking system.'))

    def _validate_reason(self, reason, link):
        required = rb_settings.get('booking_reason_required')
        validate = False
        if required == BookingReasonRequiredOptions.always:
            validate = True
        elif required == BookingReasonRequiredOptions.not_for_events:
            validate = link is None
        if validate and not reason:
            raise ExpectedError(_('You must specify a reason for booking'))
