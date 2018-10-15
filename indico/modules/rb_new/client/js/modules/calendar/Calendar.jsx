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

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {bindActionCreators} from 'redux';
import {Button, ButtonGroup, Container, Grid, Popup, Sticky} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import searchBarFactory from '../../components/SearchBar';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import {actions as bookingsActions} from '../../common/bookings';
import {selectors as roomsSelectors, actions as roomsActions} from '../../common/rooms';
import {EditableTimelineItem, ElasticTimeline, TimelineHeader, TimelineItem} from '../../common/timeline';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import {actions as filtersActions} from '../../common/filters';
import {selectors as userSelectors} from '../../common/user';

import './Calendar.module.scss';


const SearchBar = searchBarFactory('calendar', calendarSelectors);

class Calendar extends React.Component {
    static propTypes = {
        calendarData: PropTypes.object.isRequired,
        datePicker: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchCalendar: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            setMode: PropTypes.func.isRequired,
            openRoomDetails: PropTypes.func.isRequired,
            openBookRoom: PropTypes.func.isRequired,
            setFilterParameter: PropTypes.func.isRequired,
            openBookingDetails: PropTypes.func.isRequired,
        }).isRequired,
        filters: PropTypes.object.isRequired,
        hasFavoriteRooms: PropTypes.bool.isRequired,
    };


    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {
        showUnused: true,
    };

    componentDidMount() {
        const {actions: {fetchCalendar}} = this.props;
        fetchCalendar();
    }

    componentDidUpdate({datePicker: {selectedDate: prevDate, mode: prevMode}, filters: prevFilters}) {
        const {datePicker: {selectedDate, mode}, actions: {fetchCalendar}, filters} = this.props;
        const filtersChanged = !_.isEqual(prevFilters, filters);
        if (prevDate !== selectedDate || mode !== prevMode || filtersChanged) {
            fetchCalendar(filtersChanged);
        }
    }

    _getRowSerializer(day) {
        return ({bookings, preBookings, nonbookablePeriods, unbookableHours, blockings, room}) => ({
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
        const {datePicker: {selectedDate}, actions: {openBookRoom}} = this.props;
        openBookRoom(id, {
            dates: {
                startDate: moment(selectedDate, 'YYYY-MM-DD'),
                endDate: null,
            },
            timeSlot: {
                startTime: slotStartTime,
                endTime: slotEndTime,
            },
            recurrence: {
                type: 'single',
            },
        });
    };

    toggleShowUnused = () => {
        const {showUnused} = this.state;
        this.setState({showUnused: !showUnused});
    };

    render() {
        const {
            isFetching,
            calendarData: {
                rows
            },
            actions: {
                openRoomDetails, setDate, setFilterParameter, openBookingDetails, setMode
            },
            datePicker,
            hasFavoriteRooms,
            filters: {
                onlyFavorites
            }
        } = this.props;
        const {selectedDate} = datePicker;
        const {showUnused} = this.state;
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
                                <Grid.Row>
                                    <div className="filter-row">
                                        <div styleName="calendar-filters">
                                            <ButtonGroup size="large">
                                                <Button size="large" icon="filter" disabled />
                                                <Popup trigger={<Button size="large"
                                                                        primary={!showUnused}
                                                                        icon={showUnused ? 'minus square outline' : 'plus square outline'}
                                                                        onClick={this.toggleShowUnused} />}
                                                       content={showUnused ? 'Hide unused rooms' : 'Show unused rooms'} />
                                                <Popup trigger={<Button size="large"
                                                                        icon="star"
                                                                        primary={onlyFavorites}
                                                                        disabled={!onlyFavorites && !hasFavoriteRooms}
                                                                        onClick={() => setFilterParameter('onlyFavorites', !onlyFavorites)} />}
                                                       content={Translate.string('Show only my favorite rooms')} />
                                            </ButtonGroup>
                                        </div>
                                        <SearchBar />
                                    </div>
                                </Grid.Row>
                                <TimelineHeader activeDate={selectedDate ? moment(selectedDate) : moment()}
                                                setMode={setMode}
                                                mode={datePicker.mode}
                                                onDateChange={setDate}
                                                legendLabels={legendLabels} />
                            </Sticky>
                            <ElasticTimeline availability={rows}
                                             datePicker={datePicker}
                                             onClickLabel={openRoomDetails}
                                             isLoading={isFetching}
                                             onClickReservation={openBookingDetails}
                                             itemClass={datePicker.mode === 'day' ? EditableTimelineItem : TimelineItem}
                                             itemProps={{onAddSlot: this.onAddSlot}}
                                             showUnused={showUnused}
                                             longLabel />
                        </div>
                    </Container>
                </Grid.Row>
            </Grid>
        );
    }
}


export default connect(
    state => ({
        isFetching: calendarSelectors.isFetching(state),
        calendarData: calendarSelectors.getCalendarData(state),
        filters: calendarSelectors.getFilters(state),
        rooms: roomsSelectors.getAllRooms(state),
        hasFavoriteRooms: userSelectors.hasFavoriteRooms(state),
        datePicker: calendarSelectors.getDatePickerInfo(state)
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            setDate: (date) => calendarActions.setDate(serializeDate(date)),
            setMode: calendarActions.setMode,
            openRoomDetails: roomsActions.openRoomDetails,
            openBookRoom: bookRoomActions.openBookRoom,
            setFilterParameter: (param, value) => filtersActions.setFilterParameter('calendar', param, value),
            openBookingDetails: bookingsActions.openBookingDetails,
        }, dispatch),
    }),
)(Calendar);
