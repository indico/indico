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

from copy import deepcopy
from datetime import datetime, timedelta
from operator import attrgetter

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property

from MaKaC.common.Configuration import Config
from MaKaC.user import AvatarHolder
from MaKaC.webinterface.wcomponents import WTemplated

from indico.core.db import db
from indico.modules.rb.models import utils
from indico.modules.rb.models.utils import apply_filters, RBFormatter
from indico.modules.rb.models.reservation_attributes import ReservationAttribute
from indico.modules.rb.models.reservation_edit_logs import ReservationEditLog
from indico.modules.rb.models.reservation_excluded_days import ReservationExcludedDay

# old imports
from BTrees.OOBTree import OOSet
from ZODB import FileStorage, DB
from ZODB.DB import DB, transaction
from ZODB.PersistentMapping import PersistentMapping
from persistent import Persistent
from pytz import timezone
from datetime import datetime

from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_tools import qbeMatch, containsExactly_OR_containsAny, fromUTC
from MaKaC.rb_location import CrossLocationQueries
from MaKaC.plugins.RoomBooking.default.factory import Factory
from indico.core.logger import Logger
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.base import Observable
from MaKaC.plugins.RoomBooking.notifications import ReservationStartEndNotification

from indico.modules.scheduler import Client, tasks


class RepeatUnit(object):
    NEVER, HOUR, DAY, WEEK, MONTH, YEAR = xrange(6)


class Reservation(db.Model):
    __tablename__ = 'reservations'

    # columns

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # dates
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
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
    reason = db.Column(
        db.String,
        nullable=False
    )

    # relationships

    attributes = db.relationship(
        'ReservationAttribute',
        backref='reservation',
        cascade='all, delete-orphan'
    )

    edit_logs = db.relationship(
        'ReservationEditLog',
        backref='reservation',
        cascade='all, delete-orphan'
    )

    ed = db.relationship(
        'ReservationExcludedDay',
        backref='reservation',
        order_by=ReservationExcludedDay.excluded_day.desc(),
        cascade='all, delete-orphan'
    )
    excluded_days = association_proxy(
        'ed',
        'excluded_day',
        creator=lambda d: ReservationExcludedDay(excluded_day=d)
    )

    notifications = db.relationship(
        'ReservationNotification',
        backref='reservation',
        cascade='all, delete-orphan'
    )

    # TODO
    def __str__(self):
        s = """
               id: {self.id}

             room: {room_name}
       start_date: {start_date}
         end_date: {end_date}
        createdDT: {created_at}

      repeat_unit: {self.repeat_unit}
    repeatability: {self.repeatability}
          weekDay: {self.weekDay}
       weekNumber: {self.weekNumber}

    bookedForName: {self.bookedForName}
     contactEmail: {self.contactEmail}
     contactPhone: {self.contactPhone}
        createdBy: {self.createdBy}
           reason: {self.reason}

       isRejected: {self.isRejected}
      isCancelled: {self.isCancelled}

      isConfirmed: {is_confirmed}
          isValid: {is_valid}
       isArchival: {self.is_archival}
          isHeavy: {self.is_heavy}
"""
        return utils.formatString(s, self)

    def __repr__(self):
        return '<Reservation({0}, {1}, {2}, {3}, {4})>'.format(
            self.id,
            self.room_id,
            self.booked_for_name,
            self.start_date,
            self.end_date
        )

    @hybrid_property
    def is_live(self):
        return self.end_date >= datetime.utcnow()

    def is_archival(self):
        return not self.is_live()

    @hybrid_property
    def is_repeating(self):
        return self.repeat_unit != RepeatUnit.NEVER

    def addEditLog(self, edit_log):
        self.edit_logs.append(edit_log)

    def removeEditLog(self, edit_log):
        self.edit_logs.remove(edit_log)

    def clearEditLogs(self):
        del self.edit_logs[:]

    def addExcludedDate(self, excluded_date):
        self.excluded_dates.append(excluded_date)

    def removeExcludedDate(self, excluded_date):
        self.excluded_dates.remove(excluded_date)

    def clearExcludedDates(self):
        del self.excluded_dates[:]

    def getRepetitions(self):
        pass

    @staticmethod
    def getReservationById(rid):
        return Reservation.query.get(rid)

    @staticmethod
    @utils.filtered
    def getReservations(**filters):
        return Reservation, Reservation.query

    @staticmethod
    def getOverlappingPeriods(start_date, end_date):
        return Reservation.getReservations(**locals())

    def getCreator(self):
        return AvatarHolder().getById(self.created_by)

    def getBookedForUser(self):
        return AvatarHolder().getById(self.booked_for_id)

    def setBookedForUser(self, avatar):
        self.booked_for_id = avatar and avatar.getId()

    def getContactEmailList(self):
        email_list = self.contact_email
        if email_list:
            return email_list.split(',')

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

    # emails

    def getNotificationEmailList(self):
        notification_list = self.getAttributeByName('notification email')
        if notification_list:
            return notification_list.split(',')
        return []

    def _getEmailDateAndOccurrenceText(self, date=None):
        if date:
            occurrence_text = '(SINGLE OCCURRENCE)'
            formatted_start_date = formatDate(date)
        else:
            occurrence_text = ''
            try:
                formatted_start_date = formatDateTime(self.start_date)
            except:
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
            # toList
            to = creator.getEmail()
            to2 = self.getContactEmailList()

            # subject
            subject = self._getEmailSubject()

            # content
            body = WTemplated(mail_params.get('template_name')).getHTML(
                dict(mail_params, **{
                    'reservation': self,
                    'firstName': creator.getFirstName()
                })
            )

            # mail
            return {
                'fromAddr': Config.getInstance.getNoReplyEmail(),
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
            'fromAddr': Config.getInstance.getNoReplyEmail(),
            'toList': set(
                [self.room.getResponsible().getEmail()] +
                self.getNotificationEmailList()
            ),
            'subject': subject,
            'body': body
        }

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
                    'fromAddr': Config.getInstance.getNoReplyEmail(),
                    'toList': to,
                    'subject': subject,
                    'body': body
                }

    def _getAssistanceEmail(self, **mail_params):
        to = utils.getRoomBookingOption('assistanceNotificationEmails')
        if (to and self.room.notification_for_assistance and
            (self.getAttributeByName('needsAssistance') or
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
                'fromAddr': Config.getInstance.getNoReplyEmail(),
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

        return filter(None, list(
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
        ))

    def notifyAboutCancellation(self, date=None):
        """
        Notifies (e-mails) user and responsible about
        reservation cancellation.
        Called after cancel().
        """

        formatted_start_date, occurrence_text = self._getEmailDateAndOccurrenceText(date=date)

        return filter(None, list(
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
        ))


    def notifyAboutRejection(self, date=None, reason=None):
        """
        Notifies (e-mails) user and responsible about
        reservation rejection.
        Called after reject().
        """

        formatted_start_date, occurrence_text = self._getEmailDateAndOccurrenceText(date=date)

        return filter(None, list(
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
        ))

    def notifyAboutConfirmation(self):
        """
        Notifies (e-mails) user about reservation acceptance.
        Called after reject().
        """

        return filter(None, list(
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
        ))

    def notifyAboutUpdate(self, attrsBefore):
        """
        Notifies (e-mails) user and responsible about
        reservation update.
        Called after update().
        """

        is_cancelled = (attrsBefore.get('needsAssistance', False) and
                        not self.getAttributeByName('needsAssistance'))

        return filter(None, list(
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
        ))

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

    def getCollisions(self):
        pass

    @utils.filtered
    def getExcludedDays(self, **filters):
        return ReservationExcludedDay, self.excluded_days.query

    def setExcludedDays(self, excluded_days):
        self.clearCalendarCache()
        self.excluded_days = map(lambda excluded_day: ReservationExcludedDay(excluded_day=excluded_day),
            excluded_days)

    def addExcludedDay(self, excluded_day):
        self.clearCalendarCache()
        self.excluded_days.append(excluded_day)

    def removeExcludedDay(self, excluded_day):
        self.clearCalendarCache()
        if excluded_day in self.excluded_days:
            self.excluded_days.remove(excluded_day)

    def containsExcludedDay(self, excluded_day):
        return excluded_day in self.excluded_days

    @staticmethod
    @utils.filtered
    def getCountOfReservations(**filters):
        return len(Reservation.getReservations(**filters))

    @staticmethod
    def getClosestReservation(resvs=[], after=None):
        if not after:
            after = datetime.utcnow()
        if not resvs:
            resvs = sorted(filter(lambda r: r.start_date >= after, resvs),
                           key=attrgetter('start_date'))
            if resvs:
                return resvs[0]
        # TODO order_by limit 1
        return Reservation.getReservations(is_live=True)[0]

    def getLocator(self):
        pass

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

    def canBeModified(self, accessWrapper):
        """
        The following people are authorized to modify a booking:
        - owner (the one who created the booking)
        - responsible for a room
        - admin (of course)
        """
        if accessWrapper is None:
            return False

        user = None
        if isinstance(accessWrapper, AccessWrapper):
            user = accessWrapper.getUser()
        elif isinstance(accessWrapper, Avatar):
            user = accessWrapper
        else:
            raise MaKaCError(_('canModify requires either AccessWrapper or Avatar object'))

        if not user:
            return False
        return (user.isRBAdmin() or self.isOwnedBy(user) or
                self.room.isOwnedBy(user) or self.isBookedFor(user))

    def canBeCancelled(self, user):
        """ Owner can cancel """
        return user and (self.isOwnedBy(user) or
                         user.isRBAdmin() or self.isBookedFor(user))

    def canBeRejected(self, user):
        """ Responsible can reject """
        return user and (user.isRBAdmin() or self.room.isOwnedBy(user))

    def canBeDeleted(self, user):
        """ Only admin can delete """
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
        return self.getCreator()

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
        return (self.is_confirmed and
                not self.is_rejected and
                not self.is_cancelled)

    def is_heavy(self):
        """
        Defines when reservation is considered "heavy".

        Conditions of heavines - the booking:
        1. Is for room which is publically reservable AND
        2. Is repeating AND
        3. Lasts longer than one month AND
        4. Takes more than x hours monthly
        """
        if (not self.room.isReservable or self.room.hasBookingACL() or
            not self.is_repeating() or
            (self.end_date - self.start_date).days < 30):
            return False

        # TODO: put it into config
        HOURS_MONTHLY_TO_CONSIDER_HEAVY = 15
        totalHours = sum(lambda p: (p.endDT - p.startDT).seconds / 3600.0, self.splitToPeriods())
        hoursPerMonth = totalHours / (self.endDT - self.startDT).days * 30
        return hoursPerMonth >= HOURS_MONTHLY_TO_CONSIDER_HEAVY

    def getNotifications(self):
        return self.notifications.all()

    def getLocalizedStartDateTime(self):
        tz = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return timezone(tz).localize(self.start_date)

    def getLocalizedEndDateTime(self):
        tz = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
        return timezone(tz).localize(self.end_date)

    @staticmethod
    def getReservations(**filters):
        return apply_filters(Reservation.query, Reservation, **filters).all()

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

    @staticmethod
    def getLiveReservationCount(**filters):
        q = apply_filters(Reservation.query, Reservation, **filters)
        return q.filter_by(is_live=True).count()

    @staticmethod
    def getNumberOfArchivalReservations(**filters):
        q = apply_filters(Reservation.query, Reservation, **filters)
        return q.filter_by(is_live=False).count()

    def getLocationName(self):
        return self.room.location.name

    def addEditLog(self, e):
        self.edit_logs.append(e)

    def removeEditLogs(self):
        self.edit_logs.delete()

    def getEditLogs(self, **filters):
        return apply_filters(self.edit_logs, ReservationEditLog, **filters).all()

    def hasEditLogs(self):
        return self.edit_logs.exists()

    def getReservationModificationInformation(self, old):
        changes, info = self.getSnapShotDiff(old), []
        if change:
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
