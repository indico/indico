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


export default class TimelineItem extends React.Component {
    static propTypes = {
        startHour: PropTypes.number.isRequired,
        endHour: PropTypes.number.isRequired,
        step: PropTypes.number.isRequired,
        data: PropTypes.object.isRequired,
        onClick: PropTypes.func
    };

    static defaultProps = {
        onClick: null
    };

    calculateWidth = (startDt, endDt) => {
        const {startHour, endHour, step} = this.props;
        let segmentStartDuration = (startDt.hours() * 60) + startDt.minutes();
        let segmentEndDuration = (endDt.hours() * 60) + endDt.minutes();

        if (segmentStartDuration < startHour * 60) {
            segmentStartDuration = startHour * 60;
        }
        if (segmentEndDuration > endHour * 60) {
            segmentEndDuration = endHour * 60;
        }

        return (segmentEndDuration - segmentStartDuration) / (step * 60);
    };

    calculatePosition = (startDt) => {
        const {startHour, step} = this.props;
        let segmentStartDuration = (startDt.hours() * 60) + startDt.minutes();
        if (segmentStartDuration < startHour * 60) {
            segmentStartDuration = startHour * 60;
        }
        return (segmentStartDuration - (startHour * 60)) / (step * 60);
    };

    renderOccurrence = (occurrence, additionalClasses = '') => {
        let segmentStartDt, segmentEndDt, popupContent;
        const {start_dt: startDt, end_dt: endDt, start_time: startTime, end_time: endTime,
               reservation, reason, bookable} = occurrence;
        const {startHour, endHour, step, onClick} = this.props;
        if (additionalClasses === 'blocking') {
            segmentStartDt = moment(startHour, 'HH:mm');
            segmentEndDt = moment(endHour, 'HH:mm');
        } else if (additionalClasses === 'unbookable-hours') {
            segmentStartDt = moment(startTime, 'HH:mm');
            segmentEndDt = moment(endTime, 'HH:mm');
        } else {
            segmentStartDt = moment(startDt, 'YYYY-MM-DD HH:mm');
            segmentEndDt = moment(endDt, 'YYYY-MM-DD HH:mm');
        }
        const blockWidth = 100 / (((endHour - startHour) / step) + 1);
        const segmentWidth = this.calculateWidth(segmentStartDt, segmentEndDt) * blockWidth;
        const segmentPosition = this.calculatePosition(segmentStartDt) * blockWidth;
        if (additionalClasses === 'blocking') {
            popupContent = (
                <div styleName="popup-center">{Translate.string('Room blocked: {reason}', {reason})}</div>
            );
        } else if (additionalClasses === 'unbookable-periods') {
            popupContent = (
                <div styleName="popup-center">{Translate.string('Not possible to book in this period')}</div>
            );
        } else if (additionalClasses === 'unbookable-hours') {
            popupContent = (
                <div styleName="popup-center">
                    <div>{Translate.string('Not possible to book between:')}</div>
                    <div>{segmentStartDt.format('HH:mm')} - {segmentEndDt.format('HH:mm')}</div>
                </div>
            );
        } else {
            popupContent = (
                <div styleName="popup-center">
                    <div>
                        {segmentStartDt.format('HH:mm')} - {segmentEndDt.format('HH:mm')}
                    </div>
                    <div>
                        {reservation ? reservation.booking_reason : (bookable ? Translate.string('Click to book it') : '')}
                    </div>
                </div>
            );
        }

        const segment = (
            <div className={additionalClasses} onClick={onClick && additionalClasses === 'default' ? onClick : null}
                 styleName="timeline-occurrence"
                 style={{left: `${segmentPosition}%`, width: `calc(${segmentWidth}% + 1px)`}} />
        );
        return (
            <Popup trigger={segment} content={popupContent} position="bottom center"
                   header={reservation && reservation.booked_for_name}
                   hideOnScroll />
        );
    };

    renderOccurrences = () => {
        const {data} = this.props;
        return (
            Object.entries(data).map(([name, occurrences]) => (
                occurrences.map((occurrence, i) => (
                    // eslint-disable-next-line react/no-array-index-key
                    <React.Fragment key={i}>
                        {this.renderOccurrence(occurrence, classes[name] || 'default')}
                    </React.Fragment>
                ))
            ))
        );
    };

    render() {
        return (
            <div styleName="timeline-item">
                {this.renderOccurrences()}
            </div>
        );
    }
}
