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
import {ElasticTimeline, TimelineHeader} from '../../common/timeline';
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
        isFetchingActiveBookings: PropTypes.bool.isRequired,
        roomFilters: PropTypes.object.isRequired,
        calendarFilters: PropTypes.object.isRequired,
        localFilters: PropTypes.shape({
            hideUnused: PropTypes.bool.isRequired,
        }).isRequired,
        allowDragDrop: PropTypes.bool,
        view: PropTypes.oneOf(['timeline', 'list']).isRequired,
        actions: PropTypes.exact({
            fetchCalendar: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            setMode: PropTypes.func.isRequired,
            openRoomDetails: PropTypes.func.isRequired,
            openBookRoom: PropTypes.func.isRequired,
            openBookingDetails: PropTypes.func.isRequired,
            setFilterParameter: PropTypes.func.isRequired,
            changeView: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        allowDragDrop: true
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

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

    onAddSlot = ({room, slotStartTime, slotEndTime}) => {
        const {datePicker: {selectedDate}, actions: {openBookRoom}} = this.props;
        openBookRoom(room.id, {
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
            isPrebooking: !room.canUserBook,
        });
    };

    toggleHideUnused = () => {
        const {localFilters: {hideUnused}, actions: {setFilterParameter}} = this.props;
        setFilterParameter('hideUnused', !hideUnused);
    };

    toggleShowInactive = () => {
        const {calendarFilters: {showInactive}, actions: {setFilterParameter}} = this.props;
        setFilterParameter('showInactive', !showInactive);
    };

    renderExtraButtons = () => {
        const {
            calendarFilters: {myBookings, showInactive},
            localFilters: {hideUnused},
            actions: {setFilterParameter},
            isFetching, isFetchingActiveBookings
        } = this.props;
        const {view} = this.props;

        return (
            <Button.Group size="small">
                <Popup trigger={<Button primary={myBookings}
                                        icon="user circle"
                                        disabled={isFetching || isFetchingActiveBookings}
                                        onClick={() => setFilterParameter('myBookings', !myBookings || null)} />}>
                    <Translate>
                        Show only my bookings
                    </Translate>
                </Popup>
                {view === 'timeline' && (
                    <>
                        <Popup trigger={<Button primary={showInactive}
                                                icon="ban"
                                                disabled={isFetching}
                                                onClick={this.toggleShowInactive} />}>
                            {showInactive
                                ? <Translate>Hide rejected/cancelled bookings</Translate>
                                : <Translate>Show rejected/cancelled bookings</Translate>}
                        </Popup>
                        <Popup trigger={<Button primary={hideUnused}
                                                icon={hideUnused ? 'plus square outline' : 'minus square outline'}
                                                disabled={isFetching}
                                                onClick={this.toggleHideUnused} />}>
                            {hideUnused
                                ? <Translate>Show unused spaces</Translate>
                                : <Translate>Hide unused spaces</Translate>}
                        </Popup>
                    </>
                )}
            </Button.Group>
        );
    };

    renderViewSwitch = () => {
        const {view, actions: {changeView}, isFetching, isFetchingActiveBookings} = this.props;
        return (
            <div styleName="view-switch">
                <Popup trigger={<Button icon={<Icon name="calendar" />}
                                        primary={view === 'timeline'}
                                        onClick={() => changeView('timeline')}
                                        disabled={isFetching || isFetchingActiveBookings}
                                        size="tiny"
                                        circular />}
                       position="bottom center">
                    <Translate>
                        Show calendar view
                    </Translate>
                </Popup>
                <Popup trigger={<Button icon={<Icon name="list" />}
                                        primary={view === 'list'}
                                        onClick={() => changeView('list')}
                                        disabled={isFetching || isFetchingActiveBookings}
                                        size="tiny"
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
            view,
            isFetching,
            isFetchingActiveBookings,
            localFilters: {hideUnused},
            calendarFilters: {showInactive},
            calendarData: {rows},
            actions: {openRoomDetails, setDate, openBookingDetails, setMode},
            datePicker,
            allowDragDrop,
        } = this.props;
        const legendLabels = [
            {label: Translate.string('Booked'), color: 'orange', style: 'booking'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'},
        ];

        if (showInactive) {
            legendLabels.push(
                {label: Translate.string('Cancelled'), style: 'cancellation'},
                {label: Translate.string('Rejected'), style: 'rejection'},
            );
        }

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
                                            <RoomFilterBar disabled={isFetching || isFetchingActiveBookings} />
                                            {this.renderExtraButtons()}
                                            <SearchBar disabled={isFetching || isFetchingActiveBookings} />
                                        </div>
                                    </div>
                                    {this.renderViewSwitch()}
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
                                                 onAddSlot={editable ? this.onAddSlot : null}
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
        isFetchingActiveBookings: calendarSelectors.isFetchingActiveBookings(state),
        calendarData: calendarSelectors.getCalendarData(state),
        roomFilters: calendarSelectors.getRoomFilters(state),
        calendarFilters: calendarSelectors.getCalendarFilters(state),
        localFilters: calendarSelectors.getLocalFilters(state),
        rooms: roomsSelectors.getAllRooms(state),
        datePicker: calendarSelectors.getDatePickerInfo(state),
        view: calendarSelectors.getCalendarView(state),
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
            changeView: calendarActions.changeView,
        }, dispatch),
    }),
)(Overridable.component('Calendar', Calendar));
