// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {bindActionCreators} from 'redux';
import {Button, Container, Grid, Icon, Popup} from 'semantic-ui-react';
import {connect} from 'react-redux';
import Overridable from 'react-overridable';

import {Translate} from 'indico/react/i18n';
import {Responsive} from 'indico/react/util';
import {StickyWithScrollBack, ResponsivePopup} from 'indico/react/components';
import {serializeDate} from 'indico/utils/date';

import searchBarFactory from '../../components/SearchBar';
import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';
import {actions as bookingsActions} from '../../common/bookings';
import {actions as filtersActions} from '../../common/filters';
import {actions as roomsActions} from '../../common/rooms';
import {ElasticTimeline, TimelineHeader} from '../../common/timeline';
import CalendarListView from './CalendarListView';
import {actions as bookRoomActions} from '../bookRoom';
import {roomFilterBarFactory} from '../roomList';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';

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
    allowDragDrop: true,
  };

  constructor(props) {
    super(props);
    this.contextRef = React.createRef();
  }

  componentDidMount() {
    const {
      actions: {fetchCalendar},
    } = this.props;
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
    if (
      prevDate !== selectedDate ||
      mode !== prevMode ||
      roomFiltersChanged ||
      calendarFiltersChanged
    ) {
      fetchCalendar(roomFiltersChanged);
    }
  }

  onAddSlot = ({room, slotStartTime, slotEndTime}) => {
    const {
      datePicker: {selectedDate},
      actions: {openBookRoom},
    } = this.props;
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
    const {
      localFilters: {hideUnused},
      actions: {setFilterParameter},
    } = this.props;
    setFilterParameter('hideUnused', !hideUnused);
  };

  toggleShowInactive = () => {
    const {
      calendarFilters: {showInactive},
      actions: {setFilterParameter},
    } = this.props;
    setFilterParameter('showInactive', !showInactive);
  };

  getLegendLabels = (availability, showInactive) => {
    const inactiveTypes = showInactive ? [] : ['rejections', 'cancellations'];
    const occurrenceTypes = availability.reduce(
      (types, [, day]) => _.union(types, getOccurrenceTypes(day)),
      []
    );
    return transformToLegendLabels(occurrenceTypes, inactiveTypes);
  };

  renderExtraButtons = () => {
    const {
      calendarFilters: {myBookings, showInactive},
      localFilters: {hideUnused},
      actions: {setFilterParameter},
      isFetching,
      isFetchingActiveBookings,
    } = this.props;
    const {view} = this.props;

    return (
      <Button.Group size="small">
        <ResponsivePopup
          trigger={
            <Button
              primary={myBookings}
              icon="user circle"
              disabled={isFetching || isFetchingActiveBookings}
              onClick={() => setFilterParameter('myBookings', !myBookings || null)}
            />
          }
        >
          <Translate>Show only my bookings</Translate>
        </ResponsivePopup>
        {view === 'timeline' && (
          <>
            <ResponsivePopup
              trigger={
                <Button
                  primary={showInactive}
                  icon="ban"
                  disabled={isFetching}
                  onClick={this.toggleShowInactive}
                />
              }
            >
              {showInactive ? (
                <Translate>Hide rejected/cancelled bookings</Translate>
              ) : (
                <Translate>Show rejected/cancelled bookings</Translate>
              )}
            </ResponsivePopup>
            <ResponsivePopup
              trigger={
                <Button
                  primary={hideUnused}
                  icon={hideUnused ? 'plus square outline' : 'minus square outline'}
                  disabled={isFetching}
                  onClick={this.toggleHideUnused}
                />
              }
            >
              {hideUnused ? (
                <Translate>Show unused spaces</Translate>
              ) : (
                <Translate>Hide unused spaces</Translate>
              )}
            </ResponsivePopup>
          </>
        )}
      </Button.Group>
    );
  };

  renderViewSwitch = () => {
    const {
      view,
      actions: {changeView, setFilterParameter},
      isFetching,
      isFetchingActiveBookings,
    } = this.props;
    const timelineBtn = (
      <Button
        icon={<Icon name="calendar" />}
        primary={view === 'timeline'}
        onClick={() => changeView('timeline')}
        disabled={isFetching || isFetchingActiveBookings}
        size="small"
        circular
      />
    );
    const listBtn = (
      <Button
        icon={<Icon name="list" />}
        primary={view === 'list'}
        onClick={() => {
          setFilterParameter('showInactive', null);
          changeView('list');
        }}
        disabled={isFetching || isFetchingActiveBookings}
        size="small"
        circular
      />
    );
    return (
      <div styleName="view-switch">
        <Responsive.Tablet andLarger orElse={view === 'timeline' ? listBtn : timelineBtn}>
          <Popup trigger={timelineBtn} position="bottom center">
            <Translate>Show calendar view</Translate>
          </Popup>
          <Popup trigger={listBtn} position="bottom center">
            <Translate>Show a list of all upcoming bookings</Translate>
          </Popup>
        </Responsive.Tablet>
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
      roomFilters: {text},
      calendarData: {rows},
      actions: {openRoomDetails, setDate, openBookingDetails, setMode},
      datePicker,
      allowDragDrop,
    } = this.props;

    const editable = datePicker.mode === 'days' && allowDragDrop;
    const isTimelineVisible = view === 'timeline';
    return (
      <Grid>
        <Grid.Row styleName="row">
          <Container>
            <div ref={this.contextRef}>
              <StickyWithScrollBack context={this.contextRef.current} responsive>
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
                  <TimelineHeader
                    datePicker={datePicker}
                    disableDatePicker={isFetching || (!rows.length && !text)}
                    onModeChange={setMode}
                    onDateChange={setDate}
                    legendLabels={this.getLegendLabels(rows, showInactive)}
                  />
                )}
              </StickyWithScrollBack>
              {isTimelineVisible ? (
                <ElasticTimeline
                  availability={rows}
                  datePicker={datePicker}
                  onClickLabel={openRoomDetails}
                  isLoading={isFetching}
                  onClickReservation={openBookingDetails}
                  onAddSlot={editable ? this.onAddSlot : null}
                  showUnused={!hideUnused}
                  setDate={setDate}
                  setMode={setMode}
                  longLabel
                />
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
    datePicker: calendarSelectors.getDatePickerInfo(state),
    view: calendarSelectors.getCalendarView(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchCalendar: calendarActions.fetchCalendar,
        setDate: date => calendarActions.setDate(serializeDate(date)),
        setMode: calendarActions.setMode,
        openRoomDetails: roomsActions.openRoomDetails,
        openBookRoom: bookRoomActions.openBookRoom,
        openBookingDetails: bookingsActions.openBookingDetails,
        setFilterParameter: (name, value) =>
          filtersActions.setFilterParameter('calendar', name, value),
        changeView: calendarActions.changeView,
      },
      dispatch
    ),
  })
)(Overridable.component('Calendar', Calendar));
