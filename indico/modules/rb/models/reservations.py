# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

"""
Schema of a reservation
"""
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import OrderedMultiDict

from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy.custom import static_array
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.errors import IndicoError
from indico.modules.rb.models import utils
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate
from indico.modules.rb.models.room_equipments import (ReservationEquipmentAssociation, RoomEquipment,
                                                      RoomEquipmentAssociation)
from indico.modules.rb.models.utils import limit_groups, unimplemented, Serializer
from indico.util.date_time import now_utc, format_date, format_datetime, format_time
from indico.util.i18n import _, N_
from indico.util.string import return_ascii
from indico.web.flask.util import url_for
from MaKaC.common.Locators import Locator
from MaKaC.errors import MaKaCError
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.wcomponents import WTemplated


class ConflictingOccurrences(Exception):
    pass


class RepeatUnit(object):
    NEVER, DAY, WEEK, MONTH, YEAR = xrange(5)


class RepeatMapping(object):
    _mapping = {
        (RepeatUnit.NEVER, 0): (N_('Single reservation'), None, 'none'),
        (RepeatUnit.DAY, 1): (N_('Repeat daily'), 0, 'daily'),
        (RepeatUnit.WEEK, 1): (N_('Repeat once a week'), 1, 'weekly'),
        (RepeatUnit.WEEK, 2): (N_('Repeat once every two week'), 2, 'everyTwoWeeks'),
        (RepeatUnit.WEEK, 3): (N_('Repeat once every three week'), 3, 'everyThreeWeeks'),
        (RepeatUnit.MONTH, 1): (N_('Repeat every month'), 4, 'monthly')
    }

    @classmethod
    @unimplemented(exceptions=(KeyError,), message=_('Unimplemented repetition pair'))
    def getMessage(cls, repeat_unit, repeat_step):
        return cls._mapping[(repeat_unit, repeat_step)][0]

    @classmethod
    @unimplemented(exceptions=(KeyError,), message=_('Unimplemented repetition pair'))
    def getOldMapping(cls, repeat_unit, repeat_step):
        return cls._mapping[(repeat_unit, repeat_step)][1]

    @classmethod
    @unimplemented(exceptions=(KeyError,), message=_('Unimplemented repetition pair'))
    def get_short_name(cls, repeat_unit, repeat_step):
        # for the API
        return cls._mapping[(repeat_unit, repeat_step)][2]

    @classmethod
    @unimplemented(exceptions=(KeyError,), message=_('Unknown old repeatability'))
    def getNewMapping(cls, repeat):
        if repeat is None or repeat < 5:
            for k, (_, v, _) in cls._mapping.iteritems():
                if v == repeat:
                    return k
        else:
            raise KeyError('Undefined old repeat: {}'.format(repeat))

    @classmethod
    def getMapping(cls):
        return cls._mapping


class Reservation(Serializer, db.Model):
    __tablename__ = 'reservations'
    __public__ = []
    __calendar_public__ = [
        'id', ('booked_for_name', 'bookedForName'), ('booking_reason', 'reason'), ('details_url', 'bookingUrl')
    ]
    __api_public__ = [
        'id', ('start_date', 'startDT'), ('end_date', 'endDT'), 'repeat_unit', 'repeat_step',
        ('booked_for_name', 'bookedForName'), ('details_url', 'bookingUrl'), ('booking_reason', 'reason'),
        ('uses_video_conference', 'usesAVC'), ('needs_video_conference_setup', 'needsAVCSupport'),
        'needs_general_assistance', ('is_confirmed', 'isConfirmed'), ('is_valid', 'isValid'), 'is_cancelled',
        'is_rejected', ('location_name', 'location')
    ]

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # dates
    created_at = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    start_date = db.Column(
        db.DateTime,
        nullable=False
    )
    end_date = db.Column(
        db.DateTime,
        nullable=False
    )
    # repeatability
    repeat_unit = db.Column(
        db.SmallInteger,
        nullable=False,
        default=RepeatUnit.NEVER
    )  # week, month, year, etc.
    repeat_step = db.Column(
        db.SmallInteger,
        nullable=False,
        default=0
    )  # 1, 2, 3, etc.
    # user
    booked_for_id = db.Column(
        db.String
        # Must be nullable for legacy data :(
    )
    booked_for_name = db.Column(
        db.String,
        nullable=False
    )
    created_by = db.Column(
        db.String
        # Must be nullable for legacy data :(
    )
    # room
    room_id = db.Column(
        db.Integer,
        db.ForeignKey('rooms.id'),
        nullable=False
    )
    # reservation specific
    contact_email = db.Column(
        db.String
    )
    contact_phone = db.Column(
        db.String
    )
    is_confirmed = db.Column(
        db.Boolean,
        nullable=False
    )
    is_cancelled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_rejected = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    booking_reason = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    rejection_reason = db.Column(
        db.String
    )
    # extras
    uses_video_conference = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    needs_video_conference_setup = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    needs_general_assistance = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # relationships

    # attributes = db.relationship(
    #     'ReservationAttribute',
    #     backref='reservation',
    #     cascade='all, delete-orphan',
    #     lazy='dynamic'
    # )
    edit_logs = db.relationship(
        'ReservationEditLog',
        backref='reservation',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    occurrences = db.relationship(
        'ReservationOccurrence',
        backref='reservation',
        # This breaks update() with synchronize_session
        # order_by='ReservationOccurrence.start',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    equipments = db.relationship(
        'RoomEquipment',
        secondary=ReservationEquipmentAssociation,
        backref='reservations',
        lazy='dynamic'
    )

    # core

    @return_ascii
    def __repr__(self):
        return u'<Reservation({0}, {1}, {2}, {3}, {4})>'.format(
            self.id,
            self.room_id,
            self.booked_for_name,
            self.start_date,
            self.end_date
        )

    @hybrid_property
    def is_live(self):
        return self.end_date >= datetime.now()

    @hybrid_property
    def is_repeating(self):
        return self.repeat_unit != RepeatUnit.NEVER

    @property
    def location_name(self):
        return self.room.location.name

    @property
    def repetition(self):
        return self.repeat_unit, self.repeat_step

    @property
    def details_url(self):
        return url_for('rooms.roomBooking-bookingDetails', self, _external=True)

    @hybrid_property
    def is_archived(self):
        return self.end_date < datetime.now()

    @property
    def status_string(self):
        parts = []
        if self.is_valid:
            parts.append(_("Valid"))
        else:
            if self.is_cancelled:
                parts.append(_("Cancelled"))
            if self.is_rejected:
                parts.append(_("Rejected"))
            if not self.is_confirmed:
                parts.append(_("Not confirmed"))
        if self.is_archived:
            parts.append(_("Archived"))
        else:
            parts.append(_("Live"))
        return ', '.join(parts)

    def get_vc_equipment(self):
        vc_equipment = self.room.equipments \
                           .correlate(ReservationOccurrence) \
                           .with_entities(RoomEquipment.id) \
                           .filter_by(name='video conference') \
                           .as_scalar()
        return self.equipments.filter(RoomEquipment.parent_id == vc_equipment)

    @staticmethod
    def get_with_data(*args, **kwargs):
        filters = kwargs.pop('filters', None)
        limit = kwargs.pop('limit', None)
        offset = kwargs.pop('offset', 0)
        order = kwargs.pop('order', Reservation.start_date)
        limit_per_room = kwargs.pop('limit_per_room', False)
        if kwargs:
            raise ValueError('Unexpected kwargs: {}'.format(kwargs))

        query = Reservation.query.options(joinedload(Reservation.room))
        if filters:
            query = query.filter(*filters)
        if limit_per_room and (limit or offset):
            query = limit_groups(query, Reservation, Reservation.room_id, order, limit, offset)

        query = query.order_by(order, Reservation.created_at)

        if not limit_per_room:
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)

        result = OrderedDict((r.id, {'reservation': r}) for r in query)

        if 'vc_equipment' in args:
            vc_id_subquery = db.session.query(RoomEquipment.id) \
                .correlate(Reservation) \
                .filter_by(name='video conference') \
                .join(RoomEquipmentAssociation) \
                .filter(RoomEquipmentAssociation.c.room_id == Reservation.room_id) \
                .as_scalar()

            # noinspection PyTypeChecker
            vc_equipment_data = dict(db.session.query(Reservation.id, static_array.array_agg(RoomEquipment.name))
                                     .join(ReservationEquipmentAssociation, RoomEquipment)
                                     .filter(Reservation.id.in_(result.iterkeys()))
                                     .filter(RoomEquipment.parent_id == vc_id_subquery)
                                     .group_by(Reservation.id))

            for id_, data in result.iteritems():
                data['vc_equipment'] = vc_equipment_data.get(id_, ())

        if 'occurrences' in args:
            occurrence_data = OrderedMultiDict(db.session.query(ReservationOccurrence.reservation_id,
                                                                ReservationOccurrence)
                                               .filter(ReservationOccurrence.reservation_id.in_(result.iterkeys()))
                                               .order_by(ReservationOccurrence.start))
            for id_, data in result.iteritems():
                data['occurrences'] = occurrence_data.getlist(id_)

        return result.values()

    # reservations

    @staticmethod
    def getReservationByCreationTime(dt):
        return Reservation.query.filter_by(created_at=dt).first()

    @property
    def created_by_user(self):
        return AvatarHolder().getById(self.created_by) if self.created_by else None

    @created_by_user.setter
    def created_by_user(self, user):
        self.created_by = user.getId() if user else None

    @property
    def booked_for_user(self):
        return AvatarHolder().getById(self.booked_for_id) if self.booked_for_id else None

    @booked_for_user.setter
    def booked_for_user(self, user):
        self.booked_for_id = user.getId() if user else None

    def getCreator(self):
        return self.created_by_user

    def getBookedForUser(self):
        return self.booked_for_user

    def setBookedForUser(self, avatar):
        self.booked_for_id = avatar and avatar.getId()

    def getContactEmailList(self):
        email_list = self.contact_email
        if email_list:
            return email_list.split(',')

    # TODO: attribute names to the top
    def getNotificationEmailList(self):
        return []  # TODO: re-enable once getAttributeByName works
        notification_list = self.getAttributeByName('notification-email')
        if notification_list:
            return notification_list.value.split(',')
        return []

    def accept(self, user):
        self.is_confirmed = True
        self.add_edit_log(ReservationEditLog(user_name=user.getFullName(), info=['Reservation accepted']))

        valid_occurrences = self.occurrences.filter(ReservationOccurrence.is_valid).all()
        pre_occurrences = ReservationOccurrence.find_overlapping_with(self.room, valid_occurrences, self.id).all()
        for occurrence in pre_occurrences:
            if not occurrence.is_valid:
                continue
            occurrence.reject(u'Rejected due to collision with a confirmed reservation')

    def cancel(self, user, reason=None, log=True):
        self.is_cancelled = True
        self.rejection_reason = reason
        self.occurrences.filter_by(is_valid=True).update({'is_cancelled': True}, synchronize_session='fetch')
        if log:
            self.add_edit_log(ReservationEditLog(user_name=user.getFullName(), info=['Reservation cancelled']))

    def reject(self, user, reason, log=True):
        self.is_rejected = True
        self.rejection_reason = reason
        self.occurrences.filter_by(is_valid=True).update({'is_rejected': True, 'rejection_reason': reason},
                                                         synchronize_session='fetch')
        if log:
            log_msg = 'Reservation rejected: {}'.format(reason)
            self.add_edit_log(ReservationEditLog(user_name=user.getFullName(), info=[log_msg]))

    def notify_rejection(self, reason, occurrence_date=None):
        return self.notifyAboutRejection(occurrence_date, reason)

    def notify_cancellation(self):
        return self.notifyAboutCancellation()

    # edit logs

    def add_edit_log(self, edit_log):
        self.edit_logs.append(edit_log)

    # ================================================

    def find_excluded_days(self):
        return self.occurrences.filter(~ReservationOccurrence.is_valid)

    @staticmethod
    def find_overlapping_with(room, occurrences, reservation_id=None):
        return Reservation.find(Reservation.room == room,
                                Reservation.id != reservation_id,
                                ReservationOccurrence.is_valid,
                                ReservationOccurrence.build_overlap_criteria(occurrences),
                                _join=ReservationOccurrence)

    def find_overlapping(self):
        occurrences = self.occurrences.filter(ReservationOccurrence.is_valid).all()
        return Reservation.find_overlapping_with(self.room, occurrences, self.id)

    def get_conflicting_occurrences(self):
        valid_occurrences = self.occurrences.filter(ReservationOccurrence.is_valid).all()
        colliding_occurrences = ReservationOccurrence.find_overlapping_with(self.room, valid_occurrences, self.id).all()
        conflicts = defaultdict(lambda: dict(confirmed=[], pending=[]))
        for occurrence in valid_occurrences:
            for colliding in colliding_occurrences:
                if occurrence.overlaps(colliding):
                    key = 'confirmed' if colliding.reservation.is_confirmed else 'pending'
                    conflicts[occurrence][key].append(colliding)
        return conflicts

    def create_occurrences(self, skip_conflicts, user):
        ReservationOccurrence.create_series_for_reservation(self)
        db.session.flush()

        # Check for conflicts with nonbookable periods
        if not user.isRBAdmin():
            nonbookable_dates = self.room.nonbookable_dates.filter(NonBookableDate.end_date > self.start_date)
            for occurrence in self.occurrences:
                if not occurrence.is_valid:
                    continue
                for nbd in nonbookable_dates:
                    if nbd.overlaps(occurrence.start, occurrence.end):
                        if not skip_conflicts:
                            raise ConflictingOccurrences()
                        occurrence.cancel(user, u'Skipped due to nonbookable date', log=False, propagate=False)
                        break

        # Check for conflicts with blockings
        blocked_rooms = self.room.get_blocked_rooms(*(occurrence.start for occurrence in self.occurrences))
        for br in blocked_rooms:
            blocking = br.blocking
            if blocking.can_be_overridden(user, self.room):
                continue
            for occurrence in self.occurrences:
                if occurrence.is_valid and blocking.is_active_at(occurrence.start.date()):
                    # Cancel OUR occurrence
                    msg = u'Skipped due to collision with a blocking ({})'
                    occurrence.cancel(user, msg.format(blocking.reason), log=False, propagate=False)

        # Check for conflicts with other occurrences
        conflicting_occurrences = self.get_conflicting_occurrences()
        for occurrence, conflicts in conflicting_occurrences.iteritems():
            if not occurrence.is_valid:
                continue
            if conflicts['confirmed']:
                if not skip_conflicts:
                    raise ConflictingOccurrences()
                # Cancel OUR occurrence
                msg = u'Skipped due to collision with {} reservation(s)'
                occurrence.cancel(user, msg.format(len(conflicts['confirmed'])), log=False, propagate=False)
            elif conflicts['pending'] and self.is_confirmed:
                # Reject OTHER occurrences
                for conflict in conflicts['pending']:
                    conflict.reject(user, u'Rejected due to collision with a confirmed reservation')

    @classmethod
    def create_from_data(cls, room, data, user, prebook=None):
        """Creates a new reservation.

        :param room: The Room that's being booked.
        :param data: A dict containing the booking data, usually from a :class:`NewBookingConfirmForm` instance
        :param user: The :class:`Avatar` who creates the booking.
        :param prebook: Instead of determining the booking type from the user's
                        permissions, always use the given mode.
        """

        populate_fields = ('start_date', 'end_date', 'repeat_unit', 'repeat_step', 'room_id', 'booked_for_id',
                           'contact_email', 'contact_phone', 'booking_reason', 'equipments',
                           'needs_general_assistance', 'uses_video_conference', 'needs_video_conference_setup')

        if data['repeat_unit'] == RepeatUnit.NEVER and data['start_date'].date() != data['end_date'].date():
            raise ValueError('end_date != start_date for non-repeating booking')

        if prebook is None:
            prebook = not room.can_be_booked(user)
            if prebook and not room.can_be_prebooked(user):
                raise IndicoError('You cannot book this room')

        room.check_advance_days(data['end_date'].date(), user)
        room.check_bookable_times(data['start_date'].time(), data['end_date'].time(), user)

        reservation = cls()
        for field in populate_fields:
            if field in data:
                setattr(reservation, field, data[field])
        reservation.room = room
        reservation.booked_for_name = reservation.booked_for_user.getFullName()
        reservation.is_confirmed = not prebook
        reservation.created_by_user = user
        reservation.create_occurrences(True, user)
        if not any(occ.is_valid for occ in reservation.occurrences):
            raise IndicoError('Reservation has no valid occurrences')
        return reservation

    def modify(self, data, user):
        """Modifies an existing reservation.

        :param data: A dict containing the booking data, usually from a :class:`ModifyBookingForm` instance
        :param user: The :class:`Avatar` who modifies the booking.
        """

        populate_fields = ('start_date', 'end_date', 'repeat_unit', 'repeat_step', 'booked_for_id',
                           'contact_email', 'contact_phone', 'booking_reason', 'equipments',
                           'needs_general_assistance', 'uses_video_conference', 'needs_video_conference_setup')
        # fields affecting occurrences
        occurrence_fields = {'start_date', 'end_date', 'repeat_unit', 'repeat_step'}
        # fields where date and time are compared separately
        date_time_fields = {'start_date', 'end_date'}
        # fields for the repetition
        repetition_fields = {'repeat_unit', 'repeat_step'}
        # pretty names for logging
        field_names = {
            'start_date/date': "start date",
            'end_date/date': "end date",
            'start_date/time': "start time",
            'end_date/time': "end time",
            'repetition': "booking type",
            'booked_for_id': "'Booked for' user",
            'contact_email': "contact email",
            'contact_phone': "contact phone number",
            'booking_reason': "booking reason",
            'equipments': "list of equipment",
            'needs_general_assistance': "option 'General Assistance'",
            'uses_video_conference': "option 'Uses Video Conference'",
            'needs_video_conference_setup': "option 'Video Conference Setup Assistance'"
        }

        self.room.check_advance_days(data['end_date'].date(), user)
        self.room.check_bookable_times(data['start_date'].time(), data['end_date'].time(), user)

        changes = {}
        update_occurrences = False
        old_repetition = self.repeat_unit, self.repeat_step

        for field in populate_fields:
            old = getattr(self, field)
            new = data[field]
            converter = unicode
            if field == 'equipments':
                # Dynamic relationship
                old = sorted(old.all())
                converter = lambda x: ', '.join(x.name for x in x)
            if old != new:
                # Apply the change
                setattr(self, field, data[field])
                # Booked for id updates also update the (redundant) name
                if field == 'booked_for_id':
                    old = self.booked_for_name
                    new = self.booked_for_name = self.booked_for_user.getFullName()
                # If any occurrence-related field changed we need to recreate the occurrences
                if field in occurrence_fields:
                    update_occurrences = True
                # Record change for history entry
                if field in date_time_fields:
                    # The date/time fields create separate entries for the date and time parts
                    if old.date() != new.date():
                        changes[field + '/date'] = {'old': old.date(), 'new': new.date(), 'converter': format_date}
                    if old.time() != new.time():
                        changes[field + '/time'] = {'old': old.time(), 'new': new.time(), 'converter': format_time}
                elif field in repetition_fields:
                    # Repetition needs special handling since it consists of two fields but they are tied together
                    # We simply update it whenever we encounter such a change; after the last change we end up with
                    # the correct change data
                    changes['repetition'] = {'old': old_repetition, 'new': (self.repeat_unit, self.repeat_step),
                                             'converter': lambda x: RepeatMapping.getMessage(*x)}
                else:
                    changes[field] = {'old': old, 'new': new, 'converter': converter}

        if not changes:
            return False

        # Create a verbose log entry for the modification
        log = ['Booking modified']
        for field, change in changes.iteritems():
            field_title = field_names.get(field, field)
            converter = change['converter']
            old = converter(change['old'])
            new = converter(change['new'])
            if not old:
                log.append(u"The {} was set to '{}'".format(field_title, new))
            elif not new:
                log.append(u"The {} was cleared".format(field_title))
            else:
                log.append(u"The {} was changed from '{}' to '{}'".format(field_title, old, new))

        self.edit_logs.append(ReservationEditLog(user_name=user.getFullName(), info=log))

        # Recreate all occurrences if necessary
        if update_occurrences:
            cols = [col.name for col in ReservationOccurrence.__table__.columns
                    if not col.primary_key and col.name not in {'start', 'end'}]

            old_occurrences = {occ.date: occ for occ in self.occurrences}
            self.occurrences.delete(synchronize_session='fetch')
            self.create_occurrences(True, user)
            db.session.flush()
            # Restore rejection data etc. for recreated occurrences
            for occurrence in self.occurrences:
                old_occurrence = old_occurrences.get(occurrence.date)
                if old_occurrence:
                    for col in cols:
                        setattr(occurrence, col, getattr(old_occurrence, col))
            # Don't cause new notifications for the entire booking in case of daily repetition
            if self.repeat_unit == RepeatUnit.DAY and all(occ.is_sent for occ in old_occurrences.itervalues()):
                for occurrence in self.occurrences:
                    occurrence.is_sent = True

        # Sanity check so we don't end up with an "empty" booking
        if not any(occ.is_valid for occ in self.occurrences):
            raise IndicoError('Reservation has no valid occurrences')

        return True

    def getSoonestOccurrence(self, d):
        return self.occurrences.filter(ReservationOccurrence.start >= d).first()

    def getNextRepeatingWithUtil(self, current):
        if self.repeat_unit == RepeatUnit.NEVER:
            return timedelta.max
        elif self.repeat_unit == RepeatUnit.DAY:
            return current + relativedelta(days=self.repeat_step)
        elif self.repeat_unit == RepeatUnit.WEEK:
            return current + relativedelta(weeks=self.repeat_step)
        elif self.repeat_unit == RepeatUnit.MONTH:
            return current + relativedelta(months=self.srepeat_step)
        elif self.repeat_unit == RepeatUnit.YEAR:
            return current + relativedelta(years=self.repeat_step)
        raise MaKaCError(_('Unexpected repeat unit: ') + self.repeat_unit)

    @staticmethod
    def getOverlappingPeriods(start_date, end_date):
        return Reservation.getReservations(**locals())

    # def getAttributeByName(self, name):
    #     aval = (self.attributes
    #                 .with_entities(ReservationAttribute.value)
    #                 .outerjoin(ReservationAttribute.key)
    #                 .filter(
    #                     self.id == ReservationAttribute.reservation_id,
    #                     ReservationAttribute.key_id == ReservationAttributeKey.id,
    #                     ReservationAttributeKey.name == name
    #                 )
    #                 .first())
    #     if aval:
    #         return aval[0]

    # =========================================================

    # notification emails

    def _getEmailDateAndOccurrenceText(self, date=None):
        if date:
            occurrence_text = '(SINGLE OCCURRENCE)'
            formatted_start_date = format_date(date)
        else:
            occurrence_text = ''
            try:
                formatted_start_date = format_datetime(self.start_date)
            except Exception:  # XXX: why would this ever fail?!
                formatted_start_date = ''
        return formatted_start_date, occurrence_text

    def _getEmailSubject(self, **mail_params):
        return '{pre}[{room}] {sub} {fsd} {occ}'.format(
            room=self.room.getFullName(),
            pre=mail_params.get('pre_subject_message', ''),
            sub=mail_params.get('subject_message', ''),
            fsd=mail_params.get('formatted_start_date',
                                self._getEmailDateAndOccurrenceText()[0]),
            occ=mail_params.get('occurrence_text', '')
        ).strip()

    def _getCreatorAndContactEmail(self, **mail_params):
        creator = self.getCreator()
        if creator:
            to = creator.getEmail()
            to2 = self.getContactEmailList()

            subject = self._getEmailSubject()

            body = WTemplated(mail_params.get('template_name')).getHTML(
                dict(mail_params, **{
                    'reservation': self,
                    'firstName': creator.getFirstName()
                })
            )

            return {
                'fromAddr': Config.getInstance().getNoReplyEmail(),
                'toList': set((to and [to] or []) + to2),
                'subject': subject,
                'body': body
            }

    def _getResponsibleEmail(self, **mail_params):
        subject = self._getEmailSubject(**mail_params)

        body = WTemplated(mail_params.get('template_name')).getHTML(
            dict(mail_params, **{
                'reservation': self,
            })
        )
        return {
            'fromAddr': Config.getInstance().getNoReplyEmail(),
            'toList': set(
                [self.room.getResponsible().getEmail()] +
                self.getNotificationEmailList()
            ),
            'subject': subject,
            'body': body
        }

    # TODO: naming
    def _getAVCSupportEmail(self, **mail_params):
        if self.is_confirmed and self.getAttributeByName('usesAVC'):
            to = self.room.location.getSupportEmails()
            if to:
                subject = self._getEmailSubject(**mail_params)
                body = WTemplated(mail_params.get('template_name')).getHTML(
                    dict(mail_params, **{
                        'reservation': self
                    })
                )
                return {
                    'fromAddr': Config.getInstance().getNoReplyEmail(),
                    'toList': to,
                    'subject': subject,
                    'body': body
                }

    def _getAssistanceEmail(self, **mail_params):
        to = utils.getRoomBookingOption('assistanceNotificationEmails')
        if (to and self.room.notification_for_assistance and (self.getAttributeByName('needsAssistance') or
                                                              mail_params.get('old_needs_assistance', False))):
            rh = ContextManager.get('currentRH', None)
            user = rh._getUser() if rh else None
            subject = self._getEmailSubject(**mail_params)

            body = WTemplated(mail_params.get('template_name')).getHTML(
                dict(mail_params, **{
                    'reservation': self,
                    'currentUser': user
                })
            )
            return {
                'fromAddr': Config.getInstance().getNoReplyEmail(),
                'toList': to,
                'subject': subject,
                'body': body
            }

    def notifyAboutNewReservation(self):
        """
        Notifies (e-mails) user and responsible
        about creation of a new reservation.
        Called after insert().
        """

        return filter(None, [
            self._getCreatorAndContactEmail(
                subject_message=(
                    'PRE-Booking waiting Acceptance'
                    'New Booking on',
                )[self.is_confirmed],
                template_name=(
                    'RoomBookingEmail_2UserAfterPreBookingInsertion'
                    'RoomBookingEmail_2UserAfterBookingInsertion'
                )[self.is_confirmed]
            ),
            self._getResponsibleEmail(
                subject_message=(
                    'New PRE-Booking on',
                    'New Booking on'
                )[self.is_confirmed],
                booking_message=(
                    'Book',
                    'PRE-book'
                )[self.is_confirmed],
                template_name='RoomBookingEmail_2ResponsibleAfterBookingInsertion'
            ),
            self._getAVCSupportEmail(
                subject_message='New Booking on',
                template_name='RoomBookingEmail_2AVCSupportAfterBookingInsertion'
            ),
            self._getAssistanceEmail(
                pre_subject_message='[Support Request]',
                subject_message='New Booking on',
                template_name='RoomBookingEmail_AssistanceAfterBookingInsertion'
            )
        ])

    def notifyAboutCancellation(self, date=None):
        """
        Notifies (e-mails) user and responsible about
        reservation cancellation.
        Called after cancel().
        """

        formatted_start_date, occurrence_text = self._getEmailDateAndOccurrenceText(date=date)

        return filter(None, [
            self._getCreatorAndContactEmail(
                formatted_start_date=formatted_start_date,
                subject_message='Cancellation Confirmation on',
                occurrence_text=occurrence_text,
                date=date,
                template_name='RoomBookingEmail_2UserAfterBookingCancellation'
            ),
            self._getResponsibleEmail(
                formatted_start_date=formatted_start_date,
                subject_message='Cancelled Booking on',
                occurrence_text=occurrence_text,
                date=date,
                template_name='RoomBookingEmail_2ResponsibleAfterBookingCancellation'
            ),
            self._getAVCSupportEmail(
                formatted_start_date=formatted_start_date,
                subject_message='Booking Cancelled on',
                template_name='RoomBookingEmail_2AVCSupportAfterBookingCancellation'
            ),
            self._getAssistanceEmail(
                formatted_start_date=formatted_start_date,
                pre_subject_message='[Support Request Cancellation]',
                subject_message='Request Cancelled for',
                template_name='RoomBookingEmail_AssistanceAfterBookingCancellation'
            )
        ])

    def notifyAboutRejection(self, date=None, reason=None):
        """
        Notifies (e-mails) user and responsible about
        reservation rejection.
        Called after reject().
        """

        formatted_start_date, occurrence_text = self._getEmailDateAndOccurrenceText(date=date)

        return filter(None, [
            self._getCreatorAndContactEmail(
                formatted_start_date=formatted_start_date,
                subject_message='REJECTED Booking on',
                occurrence_text=occurrence_text,
                template_name='RoomBookingEmail_2UserAfterBookingRejection',
                date=date,
                reason=reason
            ),
            self._getResponsibleEmail(
                formatted_start_date=formatted_start_date,
                subject_message='Rejected Booking on',
                occurrence_text=occurrence_text,
                template_name='RoomBookingEmail_2ResponsibleAfterBookingRejection',
                date=date,
                reason=reason
            ),
            self._getAssistanceEmail(
                formatted_start_date=formatted_start_date,
                pre_subject_message='[Support Request Cancellation]',
                subject_message='Request Cancelled for',
                template_name='RoomBookingEmail_AssistanceAfterBookingRejection',
                date=date,
                reason=reason
            )
        ])

    def notifyAboutConfirmation(self):
        """
        Notifies (e-mails) user about reservation acceptance.
        Called after reject().
        """

        return filter(None, [
            self._getCreatorAndContactEmail(
                subject_message='Confirmed Booking on',
                template_name='RoomBookingEmail_2UserAfterBookingConfirmation'
            ),
            self._getResponsibleEmail(
                subject_message='Confirmed Booking on',
                template_name='RoomBookingEmail_2ResponsibleAfterBookingConfirmation'
            ),
            self._getAVCSupportEmail(
                subject_message='New Booking on',
                template_name='RoomBookingEmail_2AVCSupportAfterBookingInsertion'
            ),
            self._getAssistanceEmail(
                pre_subject_message='[Support Request]',
                subject_message='New Support on',
                template_name='RoomBookingEmail_AssistanceAfterBookingInsertion'
            )
        ])

    def notifyAboutUpdate(self, attrsBefore):
        """
        Notifies (e-mails) user and responsible about
        reservation update.
        Called after update().
        """

        is_cancelled = (attrsBefore.get('needsAssistance', False) and
                        not self.getAttributeByName('needsAssistance'))

        return filter(None, [
            self._getCreatorAndContactEmail(
                subject_message='Booking Modified on',
                template_name='RoomBookingEmail_2UserAfterBookingModification'
            ),
            self._getResponsibleEmail(
                subject_message='Booking Modified on',
                template_name='RoomBookingEmail_2ResponsibleAfterBookingModification'
            ),
            self._getAVCSupportEmail(
                subject_message='Modified booking on',
                template_name='RoomBookingEmail_2AVCSupportAfterBookingModification'
            ),
            self._getAssistanceEmail(
                pre_subject_message='[Support Request {}]'.format(
                    ('Modification', 'Cancelled')[is_cancelled]
                ),
                subject_message='Modified request for',
                template_name='RoomBookingEmail_AssistanceAfterBookingModification',
                old_needs_assistance=attrsBefore.get('needsAssistance', False),
                hasCancelled=is_cancelled
            )
        ])

    # ===============================================================

    @staticmethod
    def getClosestReservation(resvs=[], after=None):
        if not after:
            after = datetime.now()
        if not resvs:
            resvs = sorted(filter(lambda r: r.start_date >= after, resvs),
                           key=attrgetter('start_date'))
            if resvs:
                return resvs[0]
        # TODO order_by limit 1
        return Reservation.getReservations(is_live=True)[0]

    def getLocator(self):
        locator = Locator()
        locator['roomLocation'] = self.room.location_name
        locator['resvID'] = self.id
        return locator

    # access

    def isProtected(self):
        """
        The one must be logged in to do anything in RB module.
        """
        return True

    def can_be_accepted(self, user):
        return user and (user.isRBAdmin() or self.room.is_owned_by(user))

    def can_be_modified(self, user):
        if not user:
            return False
        if self.is_rejected or self.is_cancelled:
            return False
        return user.isRBAdmin() or self.created_by_user == user or self.room.is_owned_by(user) or self.isBookedFor(user)

    def can_be_cancelled(self, user):
        return user and (self.isOwnedBy(user) or user.isRBAdmin() or self.isBookedFor(user))

    def can_be_rejected(self, user):
        return user and (user.isRBAdmin() or self.room.is_owned_by(user))

    def can_be_deleted(self, user):
        return user and user.isRBAdmin()

    def isOwnedBy(self, avatar):
        """
        Returns True if avatar is the one who inserted this
        reservation. False otherwise.
        """
        return self.created_by == avatar.id

    def isBookedFor(self, user):
        """
        Returns True if user is the one who is booked for the reservation.
        False otherwise.
        """
        return user and (self.contact_email in user.getEmails() or
                         (utils.getRoomBookingOption('bookingsForRealUsers') and
                          self.booked_for_user == user))

    def getAccessKey(self):
        return ''

    def createdByUser(self):
        return self.created_by_user

    def splitToPeriods(self, end_date=None, start_date=None):
        """
        Returns the list of Periods that represent this reservation.

        For non-repeating reservations it is just the reservation period.
        For repeating ones, the list will include all repeatings.
        """
        if start_date is None:
            start_date = self.start_date - timedelta(1)
        # One day before the beginning
        start_date -= timedelta(1)

        periods = []

        while True:
            period = self.getNextRepeating(start_date)
            if period is None or (end_date is not None and period.start_date > end_date):
                return periods
            start_date = period.start_date
            periods.append(period)

    @property
    def is_valid(self):
        return self.is_confirmed and not (self.is_rejected or self.is_cancelled)

    def is_heavy(self):
        """
        Defines when reservation is considered "heavy".

        Conditions of heavines - the booking:
        1. Is for room which is publically reservable AND
        2. Is repeating AND
        3. Lasts longer than one month AND
        4. Takes more than x hours monthly
        """
        if (not self.room.isReservable or self.room.hasBookingACL() or not self.is_repeating
                or (self.end_date - self.start_date).days < 30):
            return False

        # TODO: put it into config
        HOURS_MONTHLY_TO_CONSIDER_HEAVY = 15
        totalHours = sum(lambda p: (p.endDT - p.startDT).seconds / 3600.0, self.splitToPeriods())
        hoursPerMonth = totalHours / (self.endDT - self.startDT).days * 30
        return hoursPerMonth >= HOURS_MONTHLY_TO_CONSIDER_HEAVY

    def getNotifications(self):
        return self.notifications.all()

    # reservations

    def getExcludedDays(self):
        return self.excluded_days.all()

    def setExcludedDays(self, excluded_days):
        self.excluded_days.delete()
        self.excluded_days.extend(excluded_days)

    def addExcludedDay(self, d):
        self.excluded_days.append(d)

    def removeExcludedDay(self, d):
        self.ed.filter_by(excluded_day=d).delete()

    def isDayExcluded(self, d):
        return self.ed.filter_by(excluded_day=d).exists()

    def getLocationName(self):
        return self.location_name
