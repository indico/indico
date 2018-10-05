# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import jsonify, request, session
from webargs import fields
from webargs.flaskparser import use_args, use_kwargs
from werkzeug.exceptions import Forbidden

from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb_new.operations.blockings import (approve_or_request_blocking, create_blocking,
                                                        get_room_blockings, update_blocking)
from indico.modules.rb_new.schemas import blockings_schema
from indico.web.util import jsonify_data


class RHCreateRoomBlocking(RHRoomBookingBase):
    @use_args({
        'room_ids': fields.List(fields.Int(), missing=[]),
        'start_date': fields.Date(),
        'end_date': fields.Date(),
        'reason': fields.Str(),
        'allowed_principals': fields.List(fields.Dict())
    })
    def _process(self, args):
        blocking = create_blocking(created_by=session.user, **args)
        approve_or_request_blocking(blocking)
        return jsonify_data(flash=False)


class RHUpdateRoomBlocking(RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self.blocking.can_be_modified(session.user):
            raise Forbidden

    def _process_args(self):
        self.blocking = Blocking.get_one(request.view_args['blocking_id'])

    @use_args({
        'room_ids': fields.List(fields.Int(), required=True),
        'reason': fields.Str(required=True),
        'allowed_principals': fields.List(fields.Dict(), missing=[])
    })
    def _process(self, args):
        update_blocking(self.blocking, **args)
        return jsonify(blockings_schema.dump(self.blocking, many=False).data)


class RHRoomBlockings(RHRoomBookingBase):
    @use_kwargs({
        'timeframe': fields.Str(),
        'my_rooms': fields.Bool(),
        'mine': fields.Bool()
    })
    def _process(self, timeframe, my_rooms, mine):
        filters = {'timeframe': timeframe, 'created_by': session.user if mine else None,
                   'in_rooms_owned_by': session.user if my_rooms else None}
        blockings = get_room_blockings(**filters)
        return jsonify(blockings_schema.dump(blockings).data)


class RHRoomBlocking(RHRoomBookingBase):
    def _process_args(self):
        self.blocking = Blocking.get_one(request.view_args['blocking_id'])

    def _process(self):
        return jsonify(blockings_schema.dump(self.blocking, many=False).data)
