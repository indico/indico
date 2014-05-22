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
from collections import defaultdict

from copy import deepcopy
from datetime import datetime, timedelta
from operator import attrgetter

from dateutil.relativedelta import relativedelta
from pytz import timezone
from sqlalchemy import func, or_
from sqlalchemy.ext.hybrid import hybrid_property

from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy.custom.utcdatetime import UTCDateTime
from indico.core.errors import IndicoError
from indico.modules.rb.models import utils
from indico.modules.rb.models.room_nonbookable_dates import NonBookableDate
from indico.modules.rb.models.utils import apply_filters
from indico.util.date_time import now_utc, format_date, format_datetime, overlaps
from indico.util.i18n import _, N_
from indico.util.string import return_ascii
from indico.web.flask.util import url_for
from .reservation_occurrences import ReservationOccurrence
from .room_equipments import ReservationEquipmentAssociation, RoomEquipment
from .utils import next_day_skip_if_weekend, unimplemented, Serializer
from MaKaC.common.Locators import Locator
from MaKaC.errors import MaKaCError
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.info import HelperMaKaCInfo


class ConflictingOccurrences(Exception):
    pass


class RepeatUnit(object):
    NEVER, DAY, WEEK, MONTH, YEAR = xrange(5)


class RepeatMapping(object):
    _mapping = {
        (RepeatUnit.NEVER, 0): (N_('Single reservation'), None),
        (RepeatUnit.DAY, 1): (N_('Repeat daily'), 0),
        (RepeatUnit.WEEK, 1): (N_('Repeat once a week'), 1),
        (RepeatUnit.WEEK, 2): (N_('Repeat once every two week'), 2),
        (RepeatUnit.WEEK, 3): (N_('Repeat once every three week'), 3),
        (RepeatUnit.MONTH, 1): (N_('Repeat every month'), 4)
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
    @unimplemented(exceptions=(KeyError,), message=_('Unknown old repeatability'))
    def getNewMapping(cls, repeat):
        if repeat is None or repeat < 5:
            for k, (_, v) in cls._mapping.iteritems():
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
    # repeatibility
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
        db.String,
        nullable=False
    )
    booked_for_name = db.Column(
        db.String,
        nullable=False
    )
    created_by = db.Column(
        db.String,
        nullable=False
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
        db.String,
        nullable=False,
        default=''
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
        order_by='ReservationOccurrence.start',
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
    def getReservationWithDefaults():
        dt = next_day_skip_if_weekend()

        return Reservation(
            start_date=dt,
            end_date=dt,
            repeat_unit=RepeatUnit.NEVER,
            repeat_step=0
        )

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
        notification_list = self.getAttributeByName('Notification Email')
        if notification_list:
            return notification_list.split(',')
        return []

    @staticmethod
    def getReservationById(rid):
        return Reservation.query.get(rid)

    def cancel(self):
        self.is_cancelled = True
        self.occurrences.update({'is_cancelled': True}, synchronize_session='fetch')

    def reject(self, reason):
        self.is_rejected = True
        self.rejection_reason = reason
        self.occurrences \
            .filter_by(is_cancelled=False) \
            .update({'is_cancelled': True, 'rejection_reason': reason},
                    synchronize_session='fetch')

    def notify_rejection(self, reason, occurrence_date=None):
        return self.notifyAboutRejection(occurrence_date, reason)

    def notify_cancellation(self):
        return self.notifyAboutCancellation()

    # edit logs

    def add_edit_log(self, edit_log):
        self.edit_logs.append(edit_log)

    # ================================================

    def getOccurrences(self):
        return self.occurrences.all()

    def find_excluded_days(self):
        return self.occurrences.filter(ReservationOccurrence.is_cancelled | ReservationOccurrence.is_rejected)

    def get_conflicting_occurrences(self):
        query = ReservationOccurrence.find(Reservation.room == self.room,
                                           Reservation.id != self.id,
                                           ReservationOccurrence.is_valid,
                                           _eager=ReservationOccurrence.reservation, _join=Reservation)
        criteria = []
        valid_occurrences = [occ for occ in self.occurrences if occ.is_valid]
        for occurrence in valid_occurrences:
            criteria += [
                # other starts after or at our start time         & other starts before our end time
                (ReservationOccurrence.start >= occurrence.start) & (ReservationOccurrence.start < occurrence.end),
                # other ends after our start time              & other ends before or when we end
                (ReservationOccurrence.end > occurrence.start) & (ReservationOccurrence.end <= occurrence.end)
            ]
        query = query.filter(or_(*criteria))
        colliding_occurrences = query.all()
        conflicts = defaultdict(lambda: dict(confirmed=[], pending=[]))
        for occurrence in valid_occurrences:
            for colliding in colliding_occurrences:
                if occurrence.overlaps(colliding):
                    key = 'confirmed' if colliding.reservation.is_confirmed else 'pending'
                    conflicts[occurrence][key].append(colliding)
        return conflicts

    def create_occurrences(self, skip_conflicts, check_nonbookable_dates=True):
        ReservationOccurrence.create_series_for_reservation(self)

        # Check for conflicts with nonbookable periods
        if check_nonbookable_dates:
            nonbookable_dates = self.room.nonbookable_dates.filter(NonBookableDate.end_date > self.start_date)
            for occurrence in self.occurrences:
                for nbd in nonbookable_dates:
                    # TODO: Use NonBookableDate.overlaps or remove that method
                    if overlaps((nbd.start_date, nbd.end_date), (occurrence.start, occurrence.end)):
                        if not skip_conflicts:
                            raise ConflictingOccurrences()
                        occurrence.cancel(u'Skipped due to nonbookable date')
                        break

        # Check for conflicts with other occurrences
        conflicting_occurrences = self.get_conflicting_occurrences()
        for occurrence, conflicts in conflicting_occurrences.iteritems():
            if conflicts['confirmed']:
                if not skip_conflicts:
                    raise ConflictingOccurrences()
                # Cancel OUR occurrence
                msg = u'Skipped due to collision with {} reservation(s)'
                occurrence.cancel(msg.format(len(conflicts['confirmed'])))
            elif conflicts['pending'] and self.is_confirmed:
                # Reject OTHER occurrences
                for conflict in conflicts['pending']:
                    conflict.reject(u'Rejected due to collision with a confirmed reservation')

    @classmethod
    def create_from_form(cls, room, form, user, prebook=None):
        """Creates a new reservation based on a NewbookingConfirmForm.

        :param room: The Room that's being booked.
        :param form: A :class:`NewBookingConfirmForm` instance containing the
                     data for the booking.
        :param user: The :class:`Avatar` who creates the booking.
        :param prebook: Instead of determining the booking type from the user's
                        permissions, always use the given mode.
        """

        if prebook is None:
            prebook = not room.can_be_booked(user)
            if prebook and not room.can_be_prebooked(user):
                raise IndicoError('You cannot book this room')

        reservation = cls()
        form.populate_obj(reservation, skip={'start_date', 'end_date', 'booked_for_name'}, existing_only=True)
        reservation.room = room
        reservation.booked_for_name = reservation.booked_for_user.getStraightFullName()
        reservation.is_confirmed = not prebook
        reservation.created_by_user = user
        reservation.start_date = form.start_date.data
        reservation.end_date = form.end_date.data
        if not user.isRBAdmin():
            bookable_times = room.bookable_times.all()
            if bookable_times:
                for bt in room.bookable_times:
                    if bt.fits_period(form.start_date.data.time(), form.end_date.data.time()):
                        break
                else:
                    raise IndicoError('Room cannot be booked at this time')
        reservation.create_occurrences(form.skip_conflicts.data, check_nonbookable_dates=not user.isRBAdmin())
        if not any(occ.is_valid for occ in reservation.occurrences):
            raise IndicoError('Reservation has no valid occurrences')
        return reservation

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

    def requestProlongation(self):
        """
        Heavy reservations require user confirmation every x weeks.
        This method sends user an e-mail, asking him to confirm (prolong)
        the reservation for the next x weeks.
        """

        return [self._getCreatorAndContactEmail(
            subject_message='Request for Booking Prolongation on',
            template_name='RoomBookingEmail_2UserRequestProlongation'
        )]

    def notifyAboutLackOfProlongation(self):
        """
        Notifies (e-mails) responsible that user
        did not prolong his HEAVY booking.
        """

        return [self._getCreatorAndContactEmail(
            subject_message='Consider Rejecting This Booking',
            template_name='RoomBookingEmail_2ResponsibleConsiderRejecting'
        )]

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

    def canBeViewed(self, accessWrapper):
        """
        Reservation details are public - anyone who is
        authenticated can view.
        """
        return True

    def can_be_modified(self, user):
        if not user:
            return False
        return user.isRBAdmin() or self.created_by_user == user or self.room.isOwnedBy(user) or self.isBookedFor(user)

    def can_be_cancelled(self, user):
        return user and (self.isOwnedBy(user) or user.isRBAdmin() or self.isBookedFor(user))

    def can_be_rejected(self, user):
        return user and (user.isRBAdmin() or self.room.isOwnedBy(user))

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
        return user and (self.contactEmail in user.getEmails() or
                         (utils.getRoomBookingOption('bookingsForRealUsers') and
                          self.bookedForUser == user))

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

    def is_valid(self):
        return self.is_confirmed and not self.is_rejected and not self.is_cancelled

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

    @staticmethod
    def getReservationCount(**filters):
        return apply_filters(Reservation.query, Reservation, **filters).count()

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

    def getSnapShot(self):
        """
        Creates dynamically a dictionary of the attributes of the object.
        This dictionary will be mainly used to compare the reservation
        before and after a modification
        """
        return deepcopy(self.__dict__)

    def getSnapShotDiff(self, old):
        # TODO: dictdiffer
        return list(diff(self.getSnapShot(), old))

    def getLocationName(self):
        return self.room.location.name

    def getReservationModificationInformation(self, old):
        changes, info = self.getSnapShotDiff(old), []
        if changes:
            info.append(_('Booking modified'))
            for change in changes:
                pass
                # TODO process messages
                # try:
                #     attrName = self._attrNamesMap[attr]
                # except KeyError:
                #     attrName = attr
                # try:
                #     prevValue = self._attrFormatMap[attr](attrDiff[attr]["prev"])
                # except KeyError, AttributeError:
                #     prevValue = str(attrDiff[attr]["prev"])
                # try:
                #     newValue = self._attrFormatMap[attr](attrDiff[attr]["new"])
                # except KeyError, AttributeError:
                #     newValue = str(attrDiff[attr]["new"])

                # if prevValue == "" :
                #     info.append("The %s was set to '%s'" %(attrName, newValue))
                # elif newValue == "" :
                #     info.append("The %s was cleared" %attrName)
                # else :
                #     info.append("The %s was changed from '%s' to '%s'" %(attrName, prevValue, newValue))
        return info


class Collision(object):

    def __init__(self, period, resv):
        self.start_date, self.end_date = period
        self.collides_with = resv

    def __repr__(self):
        return '<Collision({0}, {1}, {2})>'.format(
            self.start_date,
            self.end_date,
            self.collides_with.id,
        )
