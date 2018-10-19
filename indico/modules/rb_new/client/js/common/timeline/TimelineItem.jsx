/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import './TimelineItem.module.scss';


const classes = {
    candidates: 'default',
    preBookings: 'pre-booking',
    preConflicts: 'pre-booking-conflict',
    bookings: 'booking',
    conflicts: 'conflict',
    blockings: 'blocking',
    nonbookablePeriods: 'unbookable-periods',
    unbookableHours: 'unbookable-hours',
};

const types = {
    candidates: 'candidate',
    blockings: 'blocking',
    bookings: 'booking',
    nonbookablePeriods: 'unbookable-periods',
    unbookableHours: 'unbookable-hours',
};

function getKeyForOccurrence({reservation, startDt, endDt}) {
    let key = '';
    if (reservation) {
        key += `${reservation.id}-`;
    }
    return `${name}-${key}${startDt}-${endDt}`;
}

export default class TimelineItem extends React.Component {
    static propTypes = {
        startHour: PropTypes.number.isRequired,
        endHour: PropTypes.number.isRequired,
        data: PropTypes.object.isRequired,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        children: PropTypes.node,
        setSelectable: PropTypes.func
    };

    static defaultProps = {
        onClickCandidate: null,
        onClickReservation: null,
        children: [],
        setSelectable: null
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
        } else if (segStartMins > ((endHour - startHour) * 60)) {
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
            bookable
        } = occurrence;
        const {startHour, endHour, onClickCandidate, onClickReservation, room} = this.props;
        if (type === 'blocking') {
            segmentStartDt = moment(startHour, 'HH:mm');
            segmentEndDt = moment(endHour, 'HH:mm');
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
                <div styleName="popup-center">{Translate.string('Room blocked: {reason}', {reason})}</div>
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
        } else {
            let popupMessage;
            if (reservation) {
                popupMessage = reservation.bookingReason;
            } else if (bookable) {
                popupMessage = Translate.string('Click to book it');
            }
            popupContent = (
                <div styleName="popup-center">
                    <div>
                        {segmentStartDt.format('LT')} - {segmentEndDt.format('LT')}
                    </div>
                    <div>{popupMessage}</div>
                </div>
            );
        }

        const segment = (
            <div className={additionalClasses} onClick={() => {
                if (onClickCandidate && bookable && type === 'candidate') {
                    onClickCandidate(room.id);
                } else if (onClickReservation && type === 'booking') {
                    onClickReservation(reservation.id);
                }
            }}
                 styleName="timeline-occurrence"
                 style={{left: `${segmentPosition}%`, width: `calc(${segmentWidth}% + 1px)`}} />
        );

        return (
            <Popup trigger={segment} content={popupContent} position="bottom center"
                   header={reservation && reservation.bookedForName}
                   hideOnScroll />
        );
    };

    renderOccurrences = () => {
        const {data} = this.props;
        return Object.entries(data).map(([name, occurrences]) => (
            occurrences.map(occurrence => (
                <React.Fragment key={getKeyForOccurrence(occurrence)}>
                    {this.renderOccurrence(occurrence, classes[name] || 'default', types[name])}
                </React.Fragment>
            ))));
    };

    render() {
        const {
            children, startHour, endHour, data, onClickCandidate, onClickReservation, setSelectable, ...restProps
        } = this.props;
        return (
            <div styleName="timeline-item" {...restProps}>
                {children}
                {this.renderOccurrences()}
            </div>
        );
    }
}
