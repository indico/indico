// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';

import './TimelineItem.module.scss';


const classes = {
    candidates: 'available',
    preBookings: 'pre-booking',
    preConflicts: 'pre-booking-conflict',
    bookings: 'booking',
    conflicts: 'conflict',
    blockings: 'blocking',
    overridableBlockings: 'overridable-blocking',
    nonbookablePeriods: 'unbookable-periods',
    unbookableHours: 'unbookable-hours',
    cancellations: 'cancellation',
    pendingCancellations: 'pending-cancellations',
    rejections: 'rejection',
    conflictingCandidates: 'conflicting-candidates',
    other: 'other',
};

const types = {
    candidates: 'candidate',
    blockings: 'blocking',
    overridableBlockings: 'overridable-blocking',
    bookings: 'booking',
    nonbookablePeriods: 'unbookable-periods',
    unbookableHours: 'unbookable-hours',
    preBookings: 'pre-booking',
    cancellations: 'cancellation',
    pendingCancellations: 'pending-cancellations',
    rejections: 'rejection',
    conflictingCandidates: 'conflicting-candidates',
    other: 'other',
};

const reservationTypes = new Set(['booking', 'pre-booking', 'cancellation', 'rejection']);

const renderOrder = [
    'other',
    'conflictingCandidates',
    'preBookings',
    'preConflicts',
    'cancellations',
    'rejections',
    'bookings',
    'candidates',
    'conflicts',
    'overridableBlockings',
    'blockings',
    'nonbookablePeriods',
    'unbookableHours',
    'pendingCancellations',
];

function getKeyForOccurrence(name, {reservation, startTime, endTime, startDt, endDt}) {
    let key = '';
    if (reservation) {
        key += `${reservation.id}-`;
    }
    // startDt ? startDt : startTime: this handles unbookableHours which
    // don't have start/end dates only start/end times
    return `${name}-${key}${startDt || startTime}-${endDt || endTime}`;
}

class TimelineItem extends React.Component {
    static propTypes = {
        startHour: PropTypes.number.isRequired,
        endHour: PropTypes.number.isRequired,
        data: PropTypes.object.isRequired,
        room: PropTypes.object.isRequired,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        children: PropTypes.node,
        setSelectable: PropTypes.func,
        dayBased: PropTypes.bool,
    };

    static defaultProps = {
        onClickCandidate: null,
        onClickReservation: null,
        children: [],
        setSelectable: null,
        dayBased: false
    };

    calculateWidth = (startDt, endDt) => {
        const {startHour, endHour} = this.props;
        let segStartMins = (startDt.hours() * 60) + startDt.minutes();
        let segEndMins = (endDt.hours() * 60) + endDt.minutes();

        if (segStartMins < startHour * 60) {
            segStartMins = startHour * 60;
        }
        if (segEndMins > endHour * 60) {
            segEndMins = endHour * 60;
        }

        return (segEndMins - segStartMins) / ((endHour - startHour) * 60) * 100;
    };

    calculatePosition = (startDt) => {
        const {startHour, endHour} = this.props;
        const startMins = startHour * 60;
        let segStartMins = (startDt.hours() * 60) + startDt.minutes() - startMins;

        if (segStartMins < 0) {
            segStartMins = 0;
        } else if (segStartMins >= ((endHour - startHour) * 60)) {
            segStartMins = ((endHour - startHour) * 60) - 5;
        }

        return (segStartMins / ((endHour - startHour) * 60)) * 100;
    };

    renderOccurrence = (occurrence, additionalClasses = '', type = '') => {
        let segmentStartDt, segmentEndDt, popupContent;
        const {
            startDt,
            endDt,
            startTime,
            endTime,
            reservation,
            reason,
            rejectionReason,
            bookable
        } = occurrence;
        const {startHour, endHour, onClickCandidate, onClickReservation, room, dayBased} = this.props;
        if (type === 'blocking' || type === 'overridable-blocking') {
            segmentStartDt = moment(startHour, 'HH:mm');
            segmentEndDt = (endHour === 24 ? moment('23:59', 'HH:mm') : moment(endHour, 'HH:mm'));
        } else if (type === 'unbookable-hours') {
            segmentStartDt = moment(startTime, 'HH:mm');
            segmentEndDt = moment(endTime, 'HH:mm');
        } else {
            segmentStartDt = moment(startDt, 'YYYY-MM-DD HH:mm');
            segmentEndDt = moment(endDt, 'YYYY-MM-DD HH:mm');
        }
        const segmentWidth = this.calculateWidth(segmentStartDt, segmentEndDt);
        const segmentPosition = this.calculatePosition(segmentStartDt);

        if (type === 'blocking') {
            popupContent = (
                <div styleName="popup-center">{Translate.string('Space blocked: {reason}', {reason})}</div>
            );
        } else if (type === 'overridable-blocking') {
            popupContent = (
                <div styleName="popup-center">
                    <div>{Translate.string('Space blocked: {reason}', {reason})}</div>
                    <div styleName="allowed">{Translate.string('(You are allowed to make a booking)')}</div>
                </div>
            );
        } else if (type === 'unbookable-periods') {
            popupContent = (
                <div styleName="popup-center">{Translate.string('Not possible to book in this period')}</div>
            );
        } else if (type === 'unbookable-hours') {
            popupContent = (
                <div styleName="popup-center">
                    <div>{Translate.string('Not possible to book between:')}</div>
                    <div>{segmentStartDt.format('LT')} - {segmentEndDt.format('LT')}</div>
                </div>
            );
        } else if (type === 'cancellation') {
            popupContent = (
                <div styleName="popup-center">
                    <strong><Translate>Cancelled</Translate></strong>
                    {!!rejectionReason && <div>{Translate.string('Reason: {reason}', {reason: rejectionReason})}</div>}
                </div>
            );
        } else if (type === 'pending-cancellations') {
            popupContent = (
                <div styleName="popup-center">
                    <strong>
                        <Translate>This occurrence will be cancelled</Translate>
                    </strong>
                </div>
            );
        } else if (type === 'rejection') {
            popupContent = (
                <div styleName="popup-center">
                    <strong><Translate>Rejected</Translate></strong>
                    {!!rejectionReason && <div>{Translate.string('Reason: {reason}', {reason: rejectionReason})}</div>}
                </div>
            );
        } else if (type === 'conflicting-candidates') {
            popupContent = (
                <div styleName="popup-center">
                    <strong>
                        <Translate>This occurrence is conflicting with an existing booking</Translate>
                    </strong>
                </div>
            );
        } else {
            let popupMessage;
            if (reservation) {
                popupMessage = reservation.bookingReason;
            } else if (bookable) {
                popupMessage = room.canUserBook
                    ? Translate.string('Click to book it')
                    : Translate.string('Click to pre-book it');
            }
            popupContent = (
                <div styleName="popup-center">
                    {!dayBased && (
                        <div>
                            {segmentStartDt.format('LT')} - {segmentEndDt.format('LT')}
                        </div>
                    )}
                    <div>{popupMessage}</div>
                </div>
            );
        }
        const clickable = (onClickCandidate && bookable && type === 'candidate') ||
                          (onClickReservation && reservationTypes.has(type));
        const notOverflowing = ['blocking', 'overridable-blocking', 'unbookable-periods', 'unbookable-hours'];
        const overflowLeft = (!notOverflowing.includes(type) &&
                                 ((segmentStartDt.hours() * 60) + segmentStartDt.minutes()) < (startHour * 60));
        const overflowRight = (!notOverflowing.includes(type) &&
                                 ((segmentEndDt.hours() * 60) + segmentEndDt.minutes()) > (endHour * 60));
        const styleName = `timeline-occurrence ${overflowRight ? 'overflow-right' : ''} ${overflowLeft ? 'overflow-left' : ''}`;
        const segment = (
            <div className={`${additionalClasses} ${clickable ? 'clickable' : ''}`} onClick={() => {
                if (onClickCandidate && bookable && type === 'candidate') {
                    onClickCandidate(room);
                } else if (onClickReservation && reservationTypes.has(type)) {
                    onClickReservation(reservation.id);
                }
            }}
                 styleName={styleName}
                 style={{left: `${segmentPosition}%`, width: `${segmentWidth}%`}} />
        );

        return (
            <Popup trigger={segment} content={popupContent} position="bottom center"
                   header={reservation && reservation.bookedForName}
                   hideOnScroll />
        );
    };

    renderOccurrences = () => {
        const {data} = this.props;
        return renderOrder.filter((name) => name in data).map((name) => {
            const occurrences = data[name];
            return occurrences.map(occurrence => (
                <React.Fragment key={getKeyForOccurrence(name, occurrence)}>
                    {this.renderOccurrence(occurrence, classes[name] || 'default', types[name])}
                </React.Fragment>
            ));
        });
    };

    render() {
        const {
            children, startHour, endHour, data, onClickCandidate, onClickReservation,
            setSelectable, dayBased, ...restProps
        } = this.props;
        return (
            <div styleName="timeline-item" {...restProps}>
                {children}
                {this.renderOccurrences()}
            </div>
        );
    }
}

export default Overridable.component('TimelineItem', TimelineItem);
