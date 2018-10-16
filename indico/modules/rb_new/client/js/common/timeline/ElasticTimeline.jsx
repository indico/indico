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

import React from 'react';
import PropTypes from 'prop-types';
import {Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {dayRange, serializeDate, toMoment} from 'indico/utils/date';
import DailyTimelineContent from './DailyTimelineContent';
import WeeklyTimelineContent from './WeeklyTimelineContent';
import MonthlyTimelineContent from './MonthlyTimelineContent';
import TimelineItem from './TimelineItem';

import './Timeline.module.scss';


/**
 * An *elastic* implementation of a Timeline, which can provide
 * an overview by day, week or month.
 */
export default class ElasticTimeline extends React.Component {
    static propTypes = {
        availability: PropTypes.array.isRequired,
        datePicker: PropTypes.object.isRequired,
        bookingAllowed: PropTypes.bool,

        isLoading: PropTypes.bool,
        itemClass: PropTypes.func,
        itemProps: PropTypes.object,
        onClickLabel: PropTypes.func,
        onClickCandidate: PropTypes.func,
        onClickReservation: PropTypes.func,
        longLabel: PropTypes.bool,
        emptyMessage: PropTypes.node,
        lazyScroll: PropTypes.object,
        extraContent: PropTypes.node,
        showUnused: PropTypes.bool
    };

    static defaultProps = {
        emptyMessage: (
            <Message warning>
                <Translate>
                    No occurrences found
                </Translate>
            </Message>
        ),
        onClickCandidate: null,
        onClickReservation: null,
        bookingAllowed: false,
        extraContent: null,
        isLoading: false,
        itemClass: TimelineItem,
        itemProps: {},
        longLabel: false,
        onClickLabel: null,
        lazyScroll: null,
        showUnused: true
    };

    _getDayRowSerializer(dt) {
        const {bookingAllowed} = this.props;
        return ({
            candidates, preBookings, bookings, preConflicts, conflicts, blockings, nonbookablePeriods,
            unbookableHours
        }) => {
            const hasConflicts = !!(conflicts[dt] || []).length;
            return {
                candidates: candidates[dt] ? [{...candidates[dt][0], bookable: bookingAllowed && !hasConflicts}] : [],
                preBookings: preBookings[dt] || [],
                bookings: bookings[dt] || [],
                conflicts: conflicts[dt] || [],
                preConflicts: preConflicts[dt] || [],
                blockings: blockings[dt] || [],
                nonbookablePeriods: nonbookablePeriods[dt] || [],
                unbookableHours: unbookableHours[dt] || []
            };
        };
    }

    calcDailyRows() {
        const {availability, datePicker: {selectedDate, dateRange}} = this.props;

        if (this.singleRoom) {
            const roomAvailability = this.singleRoom;
            return dateRange.map(dt => ({
                ...this._getRowSerializer(dt)(roomAvailability),
                label: toMoment(dt).format('L'),
                key: dt
            }));
        }
        return availability.map(([, data]) => data).map((data) => ({
            availability: this._getDayRowSerializer(selectedDate)(data),
            label: data.room.full_name,
            key: data.room.id,
            conflictIndicator: true,
            room: data.room
        }));
    }

    calcWeeklyRows() {
        const {availability, datePicker: {selectedDate}} = this.props;
        const weekStart = toMoment(selectedDate, 'YYYY-MM-DD').startOf('week');
        const weekRange = [...Array(7).keys()].map(n => serializeDate(weekStart.clone().add(n, 'days')));
        if (!availability.length) {
            return [];
        }

        return availability.map(([, data]) => {
            const {room} = data;
            return {
                availability: weekRange.map(dt => [dt, this._getDayRowSerializer(dt)(data)]),
                label: room.full_name,
                key: room.id,
                conflictIndicator: true,
                room
            };
        });
    }

    calcMonthlyRows() {
        const {availability, datePicker: {selectedDate}} = this.props;
        const date = toMoment(selectedDate, 'YYYY-MM-DD');
        const monthStart = date.clone().startOf('month');
        const monthEnd = date.clone().endOf('month');
        const monthRange = dayRange(monthStart, monthEnd).map(d => d.format('YYYY-MM-DD'));
        if (!availability.length) {
            return [];
        }

        const d = availability.map(([, data]) => {
            const {room} = data;
            return {
                availability: monthRange.map(dt => [dt, this._getDayRowSerializer(dt)(data)]),
                label: room.full_name,
                key: room.id,
                conflictIndicator: true,
                room
            };
        });
        return d;
    }

    renderTimeline = () => {
        const {
            extraContent, onClickCandidate, onClickReservation, availability, isLoading, itemClass,
            itemProps, longLabel, onClickLabel, lazyScroll, datePicker: {minHour, maxHour, hourStep, mode},
            showUnused
        } = this.props;
        let Component = DailyTimelineContent;
        let rows = this.calcDailyRows(availability);

        if (mode === 'weeks') {
            Component = WeeklyTimelineContent;
            rows = this.calcWeeklyRows(availability);
        } else if (mode === 'months') {
            Component = MonthlyTimelineContent;
            rows = this.calcMonthlyRows(availability);
        }

        return (
            <>
                <div styleName="timeline">
                    {extraContent}
                    <Component rows={rows}
                               minHour={minHour}
                               maxHour={maxHour}
                               hourStep={hourStep}
                               onClickCandidate={onClickCandidate}
                               onClickReservation={onClickReservation}
                               itemClass={itemClass}
                               itemProps={itemProps}
                               longLabel={longLabel}
                               onClickLabel={onClickLabel}
                               isLoading={isLoading}
                               lazyScroll={lazyScroll}
                               showUnused={showUnused} />
                </div>
            </>
        );
    };

    render() {
        const {emptyMessage, isLoading, availability} = this.props;
        if (!isLoading && !availability.length) {
            return emptyMessage;
        }
        return this.renderTimeline();
    }
}
