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
import {Grid, Label} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {Translate} from 'indico/react/i18n';

import TimelineBase from '../TimelineBase';
import * as actions from '../../actions';

import '../Timeline.module.scss';


class Calendar extends React.Component {
    static propTypes = {
        fetchCalendar: PropTypes.func.isRequired,
        date: PropTypes.string,
        setDate: PropTypes.func.isRequired,
        rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        isFetching: PropTypes.bool.isRequired
    };

    static defaultProps = {
        date: null
    };

    componentDidMount() {
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
        const legend = (
            <>
                <Label color="orange">{Translate.string('Booked')}</Label>
                <Label styleName="pre-booking">{Translate.string('Pre-Booking')}</Label>
                <Label styleName="blocking">{Translate.string('Blocked')}</Label>
                <Label styleName="unbookable">{Translate.string('Not bookable')}</Label>
            </>
        );

        return (
            <Grid>
                <Grid.Row>
                    <TimelineBase minHour={6}
                                  maxHour={22}
                                  legend={legend}
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
            dispatch(actions.fetchCalendar());
        }
    })
)(Calendar);
