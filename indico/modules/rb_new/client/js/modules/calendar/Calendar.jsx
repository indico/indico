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
import {Container, Dimmer, Grid, Loader, Sticky} from 'semantic-ui-react';
import {connect} from 'react-redux';

import {Translate} from 'indico/react/i18n';
import {Preloader} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import {actions as roomsActions, selectors as roomsSelectors} from '../../common/rooms';
import {EditableTimelineItem, TimelineBase, TimelineHeader} from '../../common/timeline';
import BookFromListModal from '../../components/modals/BookFromListModal';
import {actions as modalActions} from '../../modals';

import '../../common/timeline/Timeline.module.scss';


class Calendar extends React.Component {
    static propTypes = {
        calendarData: PropTypes.shape({
            date: PropTypes.string,
            rows: PropTypes.arrayOf(PropTypes.object).isRequired,
        }).isRequired,
        isFetching: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchCalendar: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
            openRoomDetails: PropTypes.func.isRequired,
        }).isRequired,
    };


    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {};

    componentDidMount() {
        const {actions: {fetchCalendar}} = this.props;
        fetchCalendar();
    }

    componentDidUpdate({calendarData: {date: prevDate}}) {
        const {calendarData: {date}, actions: {fetchCalendar}} = this.props;
        if (prevDate !== date) {
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

    onAddSlot = ({room: {id}, slotStartTime, slotEndTime}) => {
        const {calendarData: {date}} = this.props;
        this.setState({
            bookingRoomId: id,
            modalFields: {
                dates: {
                    startDate: moment(date, 'YYYY-MM-DD'),
                    endDate: null
                },
                timeSlot: {
                    startTime: moment(slotStartTime, 'hh:mm'),
                    endTime: moment(slotEndTime, 'hh:mm')
                },
                recurrence: {type: 'single'}
            }
        });
    };

    onCloseBookingModal = () => {
        this.setState({
            bookingRoomId: null,
            modalFields: null
        });
    };

    render() {
        const {
            isFetching, calendarData: {date, rows}, actions: {setDate, fetchRoomDetails, openRoomDetails}
        } = this.props;
        const {bookingRoomId, modalFields} = this.state;
        const legendLabels = [
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];

        return (
            <Grid>
                <Grid.Row>
                    <Container>
                        <div ref={this.contextRef}>
                            <Sticky context={this.contextRef.current} className="sticky-filters">
                                <TimelineHeader activeDate={date ? moment(date) : moment()}
                                                onDateChange={setDate}
                                                legendLabels={legendLabels} />
                            </Sticky>
                            <TimelineBase rows={rows.map(this._getRowSerializer(date || serializeDate(moment())))}
                                          onClickLabel={openRoomDetails}
                                          isLoading={isFetching}
                                          itemClass={EditableTimelineItem}
                                          itemProps={{onAddSlot: this.onAddSlot}}
                                          longLabel />
                        </div>
                    </Container>
                </Grid.Row>
                {bookingRoomId && (
                    <Preloader checkCached={state => !!roomsSelectors.hasDetails(state, {roomId: bookingRoomId})}
                               action={() => fetchRoomDetails(bookingRoomId)}
                               dimmer={<Dimmer active page><Loader /></Dimmer>}>
                        {() => (
                            <BookFromListModal roomId={bookingRoomId}
                                               onClose={this.onCloseBookingModal}
                                               defaults={modalFields} />
                        )}
                    </Preloader>
                )}
            </Grid>
        );
    }
}


export default connect(
    state => ({
        isFetching: calendarSelectors.isFetching(state),
        calendarData: calendarSelectors.getCalendarData(state),
        rooms: roomsSelectors.getAllRooms(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            fetchRoomDetails: roomsActions.fetchDetails,
            setDate: (date) => calendarActions.setDate(serializeDate(date)),
            openRoomDetails: modalActions.openRoomDetails,
        }, dispatch),
    }),
)(Calendar);
