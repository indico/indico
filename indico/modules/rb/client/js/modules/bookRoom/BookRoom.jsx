// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {bindActionCreators} from 'redux';
import _ from 'lodash';
import {Button, Card, Grid, Header, Icon, Popup, Divider} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';
import Overridable from 'react-overridable';

import {Translate} from 'indico/react/i18n';
import {Slot, toClasses, IndicoPropTypes, Responsive} from 'indico/react/util';
import {serializeTime, serializeDate} from 'indico/utils/date';
import {StickyWithScrollBack, ResponsivePopup} from 'indico/react/components';

import searchBarFactory from '../../components/SearchBar';
import CardPlaceholder from '../../components/CardPlaceholder';
import BookingFilterBar from './BookingFilterBar';
import {roomFilterBarFactory} from '../../modules/roomList';
import BookingTimeline from './BookingTimeline';
import SearchResultCount from './SearchResultCount';
import {TimelineHeader} from '../../common/timeline';
import {queryStringRules as qsFilterRules} from '../../common/roomSearch';
import {rules as qsBookRoomRules} from './queryString';
import * as bookRoomActions from './actions';
import {actions as filtersActions} from '../../common/filters';
import {actions as roomsActions, RoomRenderer} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';
import * as bookRoomSelectors from './selectors';
import {mapControllerFactory, selectors as mapSelectors} from '../../common/map';
import BookingSuggestion from './BookingSuggestion';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';

import './BookRoom.module.scss';

const SearchBar = searchBarFactory('bookRoom', bookRoomSelectors);
const MapController = mapControllerFactory('bookRoom', bookRoomSelectors);
const RoomFilterBar = roomFilterBarFactory('bookRoom', bookRoomSelectors);

/* eslint-disable react/no-unused-state */
class BookRoom extends React.Component {
  static propTypes = {
    results: PropTypes.arrayOf(PropTypes.object).isRequired,
    isSearching: PropTypes.bool.isRequired,
    searchFinished: PropTypes.bool.isRequired,
    isTimelineVisible: PropTypes.bool.isRequired,
    totalResultCount: PropTypes.number.isRequired,
    unbookableResultCount: PropTypes.number.isRequired,
    filters: PropTypes.object.isRequired,
    suggestions: PropTypes.arrayOf(PropTypes.object).isRequired,
    showMap: PropTypes.bool.isRequired,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    timelineAvailability: PropTypes.array.isRequired,
    actions: PropTypes.exact({
      setFilterParameter: PropTypes.func.isRequired,
      clearTextFilter: PropTypes.func.isRequired,
      searchRooms: PropTypes.func.isRequired,
      fetchRoomSuggestions: PropTypes.func.isRequired,
      resetRoomSuggestions: PropTypes.func.isRequired,
      toggleTimelineView: PropTypes.func.isRequired,
      openRoomDetails: PropTypes.func.isRequired,
      openBookingForm: PropTypes.func.isRequired,
      setDate: PropTypes.func.isRequired,
      setTimelineMode: PropTypes.func.isRequired,
    }).isRequired,
    datePicker: PropTypes.object.isRequired,
    showSuggestions: PropTypes.bool,
    labels: PropTypes.shape({
      bookButton: IndicoPropTypes.i18n,
      preBookButton: IndicoPropTypes.i18n,
      detailsButton: IndicoPropTypes.i18n,
    }),
  };

  static defaultProps = {
    showSuggestions: true,
    labels: {
      bookButton: <Translate>Book Room</Translate>,
      preBookButton: <Translate>Pre-Book Room</Translate>,
      detailsButton: <Translate>See details</Translate>,
    },
  };

  state = {
    maxVisibleRooms: 20,
    suggestionsRequested: false,
  };

  componentDidMount() {
    const {
      actions: {searchRooms},
    } = this.props;
    searchRooms();
  }

  componentDidUpdate(prevProps) {
    const {filters: prevFilters, isAdminOverrideEnabled: prevIsAdminOverrideEnabled} = prevProps;
    const {filters, isAdminOverrideEnabled} = this.props;
    if (prevIsAdminOverrideEnabled !== isAdminOverrideEnabled || !_.isEqual(prevFilters, filters)) {
      this.restartSearch();
    }
  }

  componentWillUnmount() {
    const {
      actions: {clearTextFilter},
    } = this.props;
    clearTextFilter();
  }

  restartSearch() {
    const {
      actions: {searchRooms, resetRoomSuggestions},
    } = this.props;
    searchRooms();
    resetRoomSuggestions();
    this.setState({maxVisibleRooms: 20, suggestionsRequested: false});
  }

  openBookingForm(roomId, overrides = null, isPrebooking = false) {
    const {
      actions: {openBookingForm},
      filters: {dates, timeSlot, recurrence},
    } = this.props;
    if (!overrides) {
      openBookingForm(roomId, {isPrebooking});
      return;
    }
    // if we have overrides, we need to pass the data explicitly
    const bookingData = {dates, timeSlot, recurrence};
    if (overrides.time) {
      const {startTime, endTime} = timeSlot;
      bookingData.timeSlot = {
        startTime: serializeTime(moment(startTime, 'HH:mm').add(overrides.time, 'minutes')),
        endTime: serializeTime(moment(endTime, 'HH:mm').add(overrides.time, 'minutes')),
      };
    } else if (overrides.duration) {
      const {startTime, endTime} = timeSlot;
      bookingData.timeSlot = {
        startTime,
        endTime: serializeTime(moment(endTime, 'HH:mm').subtract(overrides.duration, 'minutes')),
      };
    } else if (overrides.shorten) {
      const {startDate, endDate} = dates;
      bookingData.dates = {
        startDate,
        endDate: serializeDate(moment(endDate, 'YYYY-MM-DD').subtract(overrides.shorten, 'days')),
      };
    }
    openBookingForm(roomId, {...bookingData, isPrebooking});
  }

  getLegendLabels(availability) {
    const occurrenceTypes = availability.reduce(
      (types, [, day]) => _.union(types, getOccurrenceTypes(day)),
      []
    );
    return transformToLegendLabels(occurrenceTypes);
  }

  renderFilters(refName) {
    const {[refName]: ref} = this.state;
    const {
      isSearching,
      totalResultCount,
      unbookableResultCount,
      results,
      isTimelineVisible,
      actions,
      datePicker,
      timelineAvailability,
    } = this.props;

    const {selectedDate} = datePicker;
    return (
      <StickyWithScrollBack context={ref} responsive>
        <div className="filter-row">
          <div className="filter-row-filters">
            <BookingFilterBar />
            <RoomFilterBar showOnlyAuthorizedFilter={false} />
            <SearchBar />
          </div>
          {this.renderViewSwitch()}
        </div>
        <SearchResultCount
          available={results.length}
          totalMatchingFilters={totalResultCount}
          isFetching={isSearching}
          unbookable={unbookableResultCount}
        />
        {isTimelineVisible && selectedDate && (
          <TimelineHeader
            datePicker={datePicker}
            disableDatePicker={isSearching}
            onDateChange={actions.setDate}
            onModeChange={actions.setTimelineMode}
            legendLabels={this.getLegendLabels(timelineAvailability)}
            isLoading={isSearching}
          />
        )}
      </StickyWithScrollBack>
    );
  }

  hasMoreRooms = (allowSuggestions = true) => {
    const {maxVisibleRooms, suggestionsRequested} = this.state;
    const {results, searchFinished} = this.props;
    if (!searchFinished) {
      return false;
    }
    return maxVisibleRooms < results.length || (allowSuggestions && !suggestionsRequested);
  };

  loadMoreRooms = () => {
    const {
      actions: {fetchRoomSuggestions},
      showSuggestions,
    } = this.props;
    const {maxVisibleRooms} = this.state;
    if (this.hasMoreRooms(false)) {
      this.setState({maxVisibleRooms: maxVisibleRooms + 20});
    } else if (showSuggestions) {
      this.setState({suggestionsRequested: true});
      fetchRoomSuggestions();
    }
  };

  get visibleRooms() {
    const {maxVisibleRooms} = this.state;
    const {results} = this.props;
    return results.slice(0, maxVisibleRooms);
  }

  get timelineButtonEnabled() {
    const {results, suggestions} = this.props;
    return !!(results.length || suggestions.length);
  }

  renderMainContent = () => {
    const {isSearching, isTimelineVisible, showSuggestions, labels} = this.props;
    const {
      actions: {openRoomDetails},
    } = this.props;

    const bookingModalBtn = room => (
      <Button circular icon="check" color="green" onClick={() => this.openBookingForm(room.id)} />
    );

    const showDetailsBtn = ({id}) => (
      <Button primary circular icon="search" onClick={() => openRoomDetails(id)} />
    );

    if (!isTimelineVisible) {
      return (
        <div
          className="ui"
          styleName="available-room-list"
          ref={ref => this.handleContextRef(ref, 'tileRef')}
        >
          {this.renderFilters('tileRef')}
          {isSearching ? (
            <CardPlaceholder.Group count={20} />
          ) : (
            <>
              <LazyScroll hasMore={this.hasMoreRooms()} loadMore={this.loadMoreRooms}>
                <RoomRenderer rooms={this.visibleRooms}>
                  {room => (
                    <Slot name="actions">
                      {room.canUserBook && (
                        <ResponsivePopup
                          trigger={bookingModalBtn(room)}
                          content={labels.bookButton}
                          position="top center"
                          hideOnScroll
                        />
                      )}
                      {room.canUserPrebook && (
                        // eslint-disable-next-line max-len
                        <Icon.Group onClick={() => this.openBookingForm(room.id, null, true)}>
                          <ResponsivePopup
                            trigger={<Button circular icon="check" color="orange" />}
                            content={labels.preBookButton}
                            position="top center"
                            hideOnScroll
                          />
                          <Icon corner name="wait" styleName="prebooking-corner-icon" />
                        </Icon.Group>
                      )}
                      <ResponsivePopup
                        trigger={showDetailsBtn(room)}
                        content={labels.detailsButton}
                        position="top center"
                        hideOnScroll
                      />
                    </Slot>
                  )}
                </RoomRenderer>
              </LazyScroll>
              {this.renderSuggestions()}
            </>
          )}
        </div>
      );
    } else {
      return (
        <div styleName="available-room-list" ref={ref => this.handleContextRef(ref, 'timelineRef')}>
          {this.renderFilters('timelineRef')}
          <BookingTimeline showSuggestions={showSuggestions} />
        </div>
      );
    }
  };

  renderSuggestions = () => {
    const {suggestions} = this.props;
    if (!suggestions.length) {
      return;
    }

    return (
      <div styleName="suggestions-container">
        <Divider horizontal>
          <Icon name="magic" styleName="divider-icon" circular />
        </Divider>
        <Header styleName="header">
          <Translate>Here are some alternatives we've found for you!</Translate>
        </Header>
        <Card.Group>
          {suggestions.map(({room, suggestions: roomSuggestions}) => (
            <BookingSuggestion
              key={room.id}
              room={room}
              suggestions={roomSuggestions}
              onClick={(overrides = null) => {
                this.openBookingForm(room.id, overrides, !room.canUserBook);
              }}
            />
          ))}
        </Card.Group>
      </div>
    );
  };

  renderViewSwitch() {
    const {isTimelineVisible} = this.props;
    const classes = toClasses({active: isTimelineVisible, disabled: !this.timelineButtonEnabled});

    const listBtn = (
      <Button
        icon={<Icon name="grid layout" styleName="switcher-icon" />}
        className={toClasses({active: !isTimelineVisible})}
        onClick={this.switchToRoomList}
        size="small"
        circular
      />
    );
    const timelineBtn = (
      <Button
        icon={
          <Icon
            name="calendar outline"
            styleName="switcher-icon"
            disabled={!this.timelineButtonEnabled}
          />
        }
        className={classes}
        onClick={this.switchToTimeline}
        size="small"
        circular
      />
    );
    return (
      <div styleName="view-icons">
        <Responsive.Tablet andLarger orElse={isTimelineVisible ? listBtn : timelineBtn}>
          <span styleName="icons-wrapper">
            {isTimelineVisible ? (
              <Popup trigger={listBtn} content={Translate.string('List view')} />
            ) : (
              listBtn
            )}
            {!isTimelineVisible ? (
              <Popup trigger={timelineBtn} content={Translate.string('Timeline view')} />
            ) : (
              timelineBtn
            )}
          </span>
        </Responsive.Tablet>
      </div>
    );
  }

  switchToRoomList = () => {
    const {
      actions: {toggleTimelineView},
      isTimelineVisible,
    } = this.props;
    if (isTimelineVisible) {
      toggleTimelineView(false);
      this.setState({timelineRef: null});
      this.restartSearch();
    }
  };

  switchToTimeline = () => {
    const {
      actions: {toggleTimelineView},
      isTimelineVisible,
    } = this.props;
    if (!isTimelineVisible && this.timelineButtonEnabled) {
      toggleTimelineView(true);
      this.setState({tileRef: null});
    }
  };

  handleContextRef = (ref, kind) => {
    if (kind in this.state) {
      const {[kind]: context} = this.state;
      if (context !== null) {
        return;
      }
    }
    this.setState({[kind]: ref});
  };

  render() {
    const {showMap} = this.props;
    return (
      <Grid columns={2}>
        <Grid.Column computer={showMap ? 11 : 16} mobile={16}>
          {this.renderMainContent()}
        </Grid.Column>
        {showMap && (
          <Responsive.Desktop andLarger>
            <Grid.Column computer={5} only="computer">
              <MapController
                onRoomClick={({id, canUserBook}) => this.openBookingForm(id, null, !canUserBook)}
              />
            </Grid.Column>
          </Responsive.Desktop>
        )}
      </Grid>
    );
  }
}

const mapStateToProps = state => {
  return {
    isTimelineVisible: bookRoomSelectors.isTimelineVisible(state),
    filters: bookRoomSelectors.getFilters(state),
    results: bookRoomSelectors.getSearchResultsWithoutUnbookable(state),
    suggestions: bookRoomSelectors.getSuggestions(state),
    totalResultCount: bookRoomSelectors.getTotalResultCount(state),
    unbookableResultCount: bookRoomSelectors.getUnbookableResultCount(state),
    isSearching: bookRoomSelectors.isSearchingOrCheckingPermissions(state),
    searchFinished: bookRoomSelectors.isSearchAndPermissionCheckFinished(state),
    queryString: stateToQueryString(state.bookRoom, qsFilterRules, qsBookRoomRules),
    showMap: mapSelectors.isMapVisible(state),
    dateRange: bookRoomSelectors.getTimelineDateRange(state),
    datePicker: bookRoomSelectors.getTimelineDatePicker(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    timelineAvailability: bookRoomSelectors.getTimelineAvailability(state),
  };
};

const mapDispatchToProps = dispatch => ({
  actions: bindActionCreators(
    {
      searchRooms: bookRoomActions.searchRooms,
      clearTextFilter: () => filtersActions.setFilterParameter('bookRoom', 'text', null),
      fetchRoomSuggestions: bookRoomActions.fetchRoomSuggestions,
      resetRoomSuggestions: bookRoomActions.resetRoomSuggestions,
      setFilterParameter: (param, value) =>
        filtersActions.setFilterParameter('bookRoom', param, value),
      toggleTimelineView: bookRoomActions.toggleTimelineView,
      openRoomDetails: roomsActions.openRoomDetailsBook,
      openBookingForm: bookRoomActions.openBookingForm,
      setDate: date => bookRoomActions.setTimelineDate(serializeDate(date)),
      setTimelineMode: bookRoomActions.setTimelineMode,
    },
    dispatch
  ),
});

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(Overridable.component('BookRoom', BookRoom));
