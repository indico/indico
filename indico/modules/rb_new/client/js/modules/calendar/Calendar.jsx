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
import PropTypes from 'prop-types';
import React from 'react';
import {bindActionCreators} from 'redux';
import {Button, Container, Grid, Icon, Popup, Sticky} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {Translate} from 'indico/react/i18n';
import {Overridable} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';
import searchBarFactory from '../../components/SearchBar';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import {actions as bookingsActions} from '../../common/bookings';
import {actions as filtersActions} from '../../common/filters';
import {selectors as roomsSelectors, actions as roomsActions} from '../../common/rooms';
import {EditableTimelineItem, ElasticTimeline, TimelineHeader, TimelineItem} from '../../common/timeline';
import CalendarListView from './CalendarListView';
import {actions as bookRoomActions} from '../bookRoom';
import {roomFilterBarFactory} from '../roomList';

import './Calendar.module.scss';


const SearchBar = searchBarFactory('calendar', calendarSelectors);
const RoomFilterBar = roomFilterBarFactory('calendar', calendarSelectors);


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
            openBookingDetails: PropTypes.func.isRequired,
            setFilterParameter: PropTypes.func.isRequired,
        }).isRequired,
        roomFilters: PropTypes.object.isRequired,
        calendarFilters: PropTypes.object.isRequired,
        localFilters: PropTypes.object.isRequired,
        allowDragDrop: PropTypes.bool
    };

    static defaultProps = {
        allowDragDrop: true
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {
        view: 'timeline',
    };

    componentDidMount() {
        const {actions: {fetchCalendar}} = this.props;
        fetchCalendar();
    }

    componentDidUpdate(prevProps) {
        const {
            datePicker: {selectedDate: prevDate, mode: prevMode},
            roomFilters: prevRoomFilters,
            calendarFilters: prevCalendarFilters,
        } = prevProps;
        const {
            datePicker: {selectedDate, mode},
            roomFilters,
            calendarFilters,
            actions: {fetchCalendar},
        } = this.props;
        const roomFiltersChanged = !_.isEqual(prevRoomFilters, roomFilters);
        const calendarFiltersChanged = !_.isEqual(prevCalendarFilters, calendarFilters);
        if (prevDate !== selectedDate || mode !== prevMode || roomFiltersChanged || calendarFiltersChanged) {
            fetchCalendar(roomFiltersChanged);
        }
    }

    onAddSlot = ({room: {id}, slotStartTime, slotEndTime}) => {
        const {datePicker: {selectedDate}, actions: {openBookRoom}} = this.props;
        openBookRoom(id, {
            dates: {
                startDate: selectedDate,
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

    toggleHideUnused = () => {
        const {localFilters: {hideUnused}, actions: {setFilterParameter}} = this.props;
        setFilterParameter('hideUnused', !hideUnused);
    };

    renderExtraButtons = () => {
        const {
            calendarFilters: {myBookings},
            localFilters: {hideUnused},
            actions: {setFilterParameter}
        } = this.props;
        const {view} = this.state;

        return (
            <>
                <Popup trigger={<Button size="large"
                                        primary={myBookings}
                                        icon="user circle"
                                        onClick={() => setFilterParameter('myBookings', !myBookings || null)} />}>
                    <Translate>
                        Show only my bookings
                    </Translate>
                </Popup>
                {view === 'timeline' && (
                    <Popup trigger={<Button size="large"
                                            primary={hideUnused}
                                            icon={hideUnused ? 'plus square outline' : 'minus square outline'}
                                            onClick={this.toggleHideUnused} />}>
                        {hideUnused
                            ? <Translate>Show unused rooms</Translate>
                            : <Translate>Hide unused rooms</Translate>}
                    </Popup>
                )}
            </>
        );
    };

    renderModeSwitch = () => {
        const {view} = this.state;
        return (
            <div>
                <Popup trigger={<Button icon={<Icon name="calendar" />}
                                        primary={view === 'timeline'}
                                        onClick={() => this.setState({view: 'timeline'})}
                                        circular />}
                       position="bottom center">
                    <Translate>
                        Show calendar view
                    </Translate>
                </Popup>
                <Popup trigger={<Button icon={<Icon name="list" />}
                                        primary={view === 'list'}
                                        onClick={() => this.setState({view: 'list'})}
                                        circular />}
                       position="bottom center">
                    <Translate>
                        Show a list of all upcoming bookings
                    </Translate>
                </Popup>
            </div>
        );
    };

    render() {
        const {
            isFetching,
            calendarData: {
                rows
            },
            localFilters: {
                hideUnused,
            },
            actions: {
                openRoomDetails, setDate, openBookingDetails, setMode
            },
            datePicker,
            allowDragDrop
        } = this.props;
        const {view} = this.state;
        const legendLabels = [
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];
        const editable = datePicker.mode === 'days' && allowDragDrop;
        const isTimelineVisible = view === 'timeline';
        return (
            <Grid>
                <Grid.Row>
                    <Container>
                        <div ref={this.contextRef}>
                            <Sticky context={this.contextRef.current} className="sticky-filters">
                                <Grid.Row styleName="calendar-filters">
                                    <div className="filter-row">
                                        <div className="filter-row-filters">
                                            <RoomFilterBar extraButtons={this.renderExtraButtons()} />
                                            <SearchBar />
                                        </div>
                                    </div>
                                    {this.renderModeSwitch()}
                                </Grid.Row>
                                {isTimelineVisible && (
                                    <TimelineHeader datePicker={datePicker}
                                                    disableDatePicker={isFetching || !rows.length}
                                                    onModeChange={setMode}
                                                    onDateChange={setDate}
                                                    legendLabels={legendLabels} />
                                )}
                            </Sticky>
                            {isTimelineVisible ? (
                                <ElasticTimeline availability={rows}
                                                 datePicker={datePicker}
                                                 onClickLabel={openRoomDetails}
                                                 isLoading={isFetching}
                                                 onClickReservation={openBookingDetails}
                                                 itemClass={editable ? EditableTimelineItem : TimelineItem}
                                                 itemProps={editable ? {onAddSlot: this.onAddSlot} : {}}
                                                 showUnused={!hideUnused}
                                                 conflictIndicator={false}
                                                 longLabel />
                            ) : (
                                <CalendarListView />
                            )}
                        </div>
                    </Container>
                </Grid.Row>
            </Grid>
        );
    }
}


export default connect(
    state => ({
        isFetching: calendarSelectors.isFetchingCalendar(state),
        calendarData: calendarSelectors.getCalendarData(state),
        roomFilters: calendarSelectors.getRoomFilters(state),
        calendarFilters: calendarSelectors.getCalendarFilters(state),
        localFilters: calendarSelectors.getLocalFilters(state),
        rooms: roomsSelectors.getAllRooms(state),
        datePicker: calendarSelectors.getDatePickerInfo(state)
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchCalendar: calendarActions.fetchCalendar,
            setDate: (date) => calendarActions.setDate(serializeDate(date)),
            setMode: calendarActions.setMode,
            openRoomDetails: roomsActions.openRoomDetails,
            openBookRoom: bookRoomActions.openBookRoom,
            openBookingDetails: bookingsActions.openBookingDetails,
            setFilterParameter: (name, value) => filtersActions.setFilterParameter('calendar', name, value),
        }, dispatch),
    }),
)(Overridable.component('Calendar', Calendar));
