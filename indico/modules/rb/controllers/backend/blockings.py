# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, request, session
from webargs import fields
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.rb.controllers import RHRoomBookingBase
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.blockings import Blocking
from indico.modules.rb.operations.blockings import create_blocking, get_room_blockings, update_blocking
from indico.modules.rb.schemas import blockings_schema
from indico.util.marshmallow import PrincipalList
from indico.web.args import use_args, use_kwargs


class RHCreateRoomBlocking(RHRoomBookingBase):
    @use_args({
        'room_ids': fields.List(fields.Int(), missing=[]),
        'start_date': fields.Date(required=True),
        'end_date': fields.Date(required=True),
        'reason': fields.Str(required=True),
        'allowed': PrincipalList(allow_groups=True, required=True),
    })
    def _process(self, args):
        blocking = create_blocking(created_by=session.user, **args)
        return jsonify(blockings_schema.dump(blocking, many=False))


class RHUpdateRoomBlocking(RHRoomBookingBase):
    def _check_access(self):
        RHRoomBookingBase._check_access(self)
        if not self.blocking.can_edit(session.user):
            raise Forbidden

    def _process_args(self):
        self.blocking = Blocking.get_or_404(request.view_args['blocking_id'])

    @use_args({
        'room_ids': fields.List(fields.Int(), required=True),
        'reason': fields.Str(required=True),
        'allowed': PrincipalList(allow_groups=True, required=True),
    })
    def _process(self, args):
        update_blocking(self.blocking, **args)
        return jsonify(blockings_schema.dump(self.blocking, many=False))


class RHRoomBlockings(RHRoomBookingBase):
    @use_kwargs({
        'timeframe': fields.Str(missing=None),
        'my_rooms': fields.Bool(missing=False),
        'mine': fields.Bool(missing=False)
    })
    def _process(self, timeframe, my_rooms, mine):
        filters = {'timeframe': timeframe, 'created_by': session.user if mine else None,
                   'in_rooms_owned_by': session.user if my_rooms else None}
        blockings = get_room_blockings(**filters)
        return jsonify(blockings_schema.dump(blockings))


class RHRoomBlockingBase(RHRoomBookingBase):
    def _process_args(self):
        self.blocking = Blocking.get_or_404(request.view_args['blocking_id'])


class RHRoomBlocking(RHRoomBlockingBase):
    def _process(self):
        return jsonify(blockings_schema.dump(self.blocking, many=False))


class RHBlockedRoomAction(RHRoomBlockingBase):
    def _process_args(self):
        RHRoomBlockingBase._process_args(self)
        self.action = request.view_args['action']
        self.blocked_room = (BlockedRoom.query
                             .with_parent(self.blocking)
                             .filter_by(room_id=request.view_args['room_id'])
                             .first_or_404())

    def _check_access(self):
        RHRoomBlockingBase._check_access(self)
        if not self.blocked_room.room.can_manage(session.user):
            raise Forbidden

    def _process(self):
        if self.action == 'accept':
            self.blocked_room.approve()
        elif self.action == 'reject':
            self.reject()
        return jsonify(blocking=blockings_schema.dump(self.blocking, many=False))

    @use_kwargs({
        'reason': fields.Str(required=True)
    })
    def reject(self, reason):
        self.blocked_room.reject(session.user, reason)


class RHDeleteBlocking(RHRoomBlockingBase):
    def _check_access(self):
        RHRoomBlockingBase._check_access(self)
        if not self.blocking.can_delete(session.user):
            raise Forbidden

    def _process(self):
        db.session.delete(self.blocking)
        return jsonify(blocking_id=self.blocking.id)
