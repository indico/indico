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
import {bindActionCreators} from 'redux';
import {Grid} from 'semantic-ui-react';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {RequestState} from 'indico/utils/redux';
import TimelineBase from '../../components/TimelineBase';
import * as calendarActions from './actions';

import '../../components/Timeline.module.scss';


class Calendar extends React.Component {
    static propTypes = {
        date: PropTypes.string,
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        isFetching: PropTypes.bool.isRequired,
        location: PropTypes.shape({
            pathname: PropTypes.string.isRequired,
            search: PropTypes.string.isRequired,
        }).isRequired,
        actions: PropTypes.shape({
            fetchCalendar: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
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
        const {date, actions: {fetchCalendar, setDate}} = this.props;
        if (!date) {
            setDate(moment());
        } else {
            fetchCalendar();
        }
    }

    _getRowSerializer(day) {
        return ({bookings, pre_bookings: preBookings, nonbookable_periods: nonbookablePeriods,
                 unbookable_hours: unbookableHours, blockings, room}) => ({
            availability: {
                preBookings: preBookings[day] || [],
                bookings: bookings[day] || [],
                nonbookablePeriods: nonbookablePeriods[day] || [],
                unbookableHours: unbookableHours || [],
                blockings: blockings[day] || []
            },
            label: room.full_name,
            key: room.id,
            room
        });
    }

    render() {
        const {date, rows, isFetching, actions: {setDate}} = this.props;
        const legendLabels = [
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
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
    ({calendar}) => ({
        isFetching: calendar.request.state === RequestState.STARTED,
        ...calendar.data,
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            setDate: (date) => calendarActions.setDate(date.format('YYYY-MM-DD')),
        }, dispatch)
    })
)(Calendar);
