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
import {Grid} from 'semantic-ui-react';
import {connect} from 'react-redux';

import TimelineBase from '../TimelineBase';
import * as actions from '../../actions';

import '../Timeline.module.scss';


class Calendar extends React.Component {
    static propTypes = {
        fetchCalendar: PropTypes.func.isRequired,
        date: PropTypes.string,
        setDate: PropTypes.func.isRequired,
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        isFetching: PropTypes.bool.isRequired,
        location: PropTypes.shape({
            pathname: PropTypes.string.isRequired,
            search: PropTypes.string.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        date: null
    };

    componentDidMount() {
        this._updateCalendar();
    }

    componentDidUpdate({location: prevLocation}) {
        const {location} = this.props;
        // this updates the calendar when
        // 1) the query string changes due to the user changing the date
        // 2) the user clicks on "calendar" again (which also causes a query string change)
        if (location.pathname === prevLocation.pathname && location.search !== prevLocation.search) {
            this._updateCalendar();
        }
    }

    _updateCalendar() {
        const {date, fetchCalendar, setDate} = this.props;
        if (!date) {
            setDate(moment());
        } else {
            fetchCalendar();
        }
    }

    _getRowSerializer(dt) {
        return ({bookings, pre_bookings: preBookings, nonbookable_periods: nonbookablePeriods,
                 unbookable_hours: unbookableHours, blockings, room}) => ({
            availability: {
                preBookings: preBookings[dt] || [],
                bookings: bookings[dt] || [],
                nonbookablePeriods: nonbookablePeriods[dt] || [],
                unbookableHours: unbookableHours || [],
                blockings: blockings[dt] || []
            },
            label: room.full_name,
            key: room.id,
            room
        });
    }

    render() {
        const {date, rows, setDate, isFetching} = this.props;
        const legendLabels = [
            {label: 'Booked', color: 'orange'},
            {label: 'Pre-Booking', style: 'pre-booking'},
            {label: 'Blocked', style: 'blocking'},
            {label: 'Not bookable', style: 'unbookable'}
        ];

        return (
            <Grid>
                <Grid.Row>
                    <TimelineBase minHour={6}
                                  maxHour={22}
                                  legendLabels={legendLabels}
                                  rows={rows.map(this._getRowSerializer(date))}
                                  activeDate={moment(date)}
                                  onDateChange={setDate}
                                  isLoading={isFetching}
                                  longLabel />
                </Grid.Row>
            </Grid>
        );
    }
}

export default connect(
    ({calendar}) => calendar,
    dispatch => ({
        fetchCalendar() {
            dispatch(actions.fetchCalendar());
        },
        setDate(date) {
            dispatch(actions.setCalendarDate(date.format('YYYY-MM-DD')));
            // dispatching the date change causes a query string update and
            // the corresponding location change will trigger a new fetch
        }
    })
)(Calendar);
