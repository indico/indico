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
import {connect} from 'react-redux';
import {Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {ElasticTimeline} from '../../common/timeline';
import {actions as roomsActions} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';
import * as bookRoomActions from './actions';
import * as bookRoomSelectors from './selectors';

import '../../common/timeline/Timeline.module.scss';

const timelinePropTypes = {
  datePicker: PropTypes.object.isRequired,
  availability: PropTypes.array.isRequired,
};

class _BookingTimelineComponent extends React.Component {
  static propTypes = {
    ...timelinePropTypes,
    clickable: PropTypes.bool,
    lazyScroll: PropTypes.object,
    isLoading: PropTypes.bool.isRequired,
    showEmptyMessage: PropTypes.bool,
    bookingAllowed: PropTypes.bool,
    actions: PropTypes.exact({
      openRoomDetails: PropTypes.func.isRequired,
      openBookingForm: PropTypes.func.isRequired,
    }).isRequired,
    fixedHeight: PropTypes.string,
    onClickReservation: PropTypes.func,
    setDate: PropTypes.func.isRequired,
    setMode: PropTypes.func.isRequired,
  };

  static defaultProps = {
    clickable: false,
    lazyScroll: null,
    showEmptyMessage: true,
    bookingAllowed: false,
    fixedHeight: null,
    onClickReservation: null,
  };

  state = {};

  handleBook = ({id, canUserBook}) => {
    const {
      actions: {openBookingForm},
    } = this.props;
    openBookingForm(id, {isPrebooking: !canUserBook});
  };

  render() {
    const {
      isLoading,
      lazyScroll,
      showEmptyMessage,
      clickable,
      datePicker,
      fixedHeight,
      actions: {openRoomDetails},
      availability,
      bookingAllowed,
      filters: {recurrence},
      onClickReservation,
      setDate,
      setMode,
    } = this.props;
    const emptyMessage = showEmptyMessage ? (
      <Message warning>
        <Translate>There are no rooms matching the criteria.</Translate>
      </Message>
    ) : null;

    return (
      datePicker.selectedDate && (
        <ElasticTimeline
          lazyScroll={lazyScroll}
          availability={availability}
          bookingAllowed={bookingAllowed}
          datePicker={datePicker}
          emptyMessage={emptyMessage}
          onClickCandidate={clickable ? this.handleBook : null}
          onClickLabel={clickable ? openRoomDetails : null}
          onClickReservation={onClickReservation}
          setDate={setDate}
          setMode={setMode}
          isLoading={isLoading}
          fixedHeight={fixedHeight}
          roomTimelineAction={recurrence.type !== 'single'}
        />
      )
    );
  }
}

export const BookingTimelineComponent = connect(
  state => ({
    filters: bookRoomSelectors.getFilters(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        openRoomDetails: roomsActions.openRoomDetailsBook,
        openBookingForm: bookRoomActions.openBookingForm,
      },
      dispatch
    ),
  })
)(_BookingTimelineComponent);

class BookingTimeline extends React.Component {
  static propTypes = {
    ...timelinePropTypes,
    isLoading: PropTypes.bool.isRequired,
    searchFinished: PropTypes.bool.isRequired,
    hasMoreTimelineData: PropTypes.bool.isRequired,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    filters: PropTypes.shape({
      dates: PropTypes.object.isRequired,
      timeSlot: PropTypes.object.isRequired,
      recurrence: PropTypes.object.isRequired,
    }).isRequired,
    actions: PropTypes.exact({
      fetchTimeline: PropTypes.func.isRequired,
      initTimeline: PropTypes.func.isRequired,
      addTimelineRooms: PropTypes.func.isRequired,
      fetchRoomSuggestions: PropTypes.func.isRequired,
    }).isRequired,
    showSuggestions: PropTypes.bool,
  };

  static defaultProps = {
    showSuggestions: true,
  };

  componentDidMount() {
    const {
      actions: {initTimeline, fetchTimeline, fetchRoomSuggestions},
      filters: {dates, timeSlot, recurrence},
      roomIds,
      suggestedRoomIds,
      searchFinished,
      showSuggestions,
    } = this.props;
    initTimeline(roomIds, dates, timeSlot, recurrence);
    if (roomIds.length) {
      fetchTimeline();
    }
    if (suggestedRoomIds.length) {
      this.processSuggestedRooms();
    } else if (searchFinished && showSuggestions) {
      fetchRoomSuggestions();
    }
  }

  componentDidUpdate(prevProps) {
    const {
      suggestedRoomIds: prevSuggestedRoomIds,
      filters: prevFilters,
      searchFinished: prevSearchFinished,
      isAdminOverrideEnabled: prevIsAdminOverrideEnabled,
    } = prevProps;
    const {
      actions: {initTimeline, fetchTimeline, fetchRoomSuggestions},
      filters,
      roomIds,
      suggestedRoomIds,
      searchFinished,
      showSuggestions,
      isAdminOverrideEnabled,
    } = this.props;
    const {dates, timeSlot, recurrence} = filters;
    // reset the timeline when filters changed
    if (!_.isEqual(prevFilters, filters)) {
      initTimeline([], dates, timeSlot, recurrence);
    }
    // we don't want to fetch timeline data until `searchRooms` finishes
    if (!searchFinished) {
      return;
    }
    if (
      prevIsAdminOverrideEnabled !== isAdminOverrideEnabled ||
      (!prevSearchFinished && searchFinished)
    ) {
      initTimeline(roomIds, dates, timeSlot, recurrence);
      if (roomIds.length) {
        fetchTimeline();
      }
      if (showSuggestions) {
        fetchRoomSuggestions();
      }
    }
    if (!_.isEqual(prevSuggestedRoomIds, suggestedRoomIds) && suggestedRoomIds.length) {
      this.processSuggestedRooms();
    }
  }

  processSuggestedRooms() {
    const {
      actions: {fetchTimeline, addTimelineRooms},
      roomIds,
      suggestedRoomIds,
    } = this.props;
    addTimelineRooms(suggestedRoomIds);
    // if we have no normal results there is no lazy scroller to trigger the fetching
    if (!roomIds.length) {
      fetchTimeline();
    }
  }

  render() {
    const {
      isLoading,
      hasMoreTimelineData,
      availability,
      datePicker,
      actions: {fetchTimeline},
      filters: {
        dates: {startDate},
      },
    } = this.props;
    const lazyScroll = {
      hasMore: hasMoreTimelineData,
      loadMore: fetchTimeline,
      isFetching: isLoading,
    };

    return (
      <BookingTimelineComponent
        lazyScroll={lazyScroll}
        isLoading={isLoading}
        availability={availability}
        datePicker={datePicker}
        defaultDate={startDate}
        showEmptyMessage={false}
        bookingAllowed
        clickable
      />
    );
  }
}

export default connect(
  state => ({
    availability: bookRoomSelectors.getTimelineAvailability(state),
    datePicker: bookRoomSelectors.getTimelineDatePicker(state),
    isLoading: bookRoomSelectors.isFetchingTimeline(state),
    searchFinished: bookRoomSelectors.isSearchAndPermissionCheckFinished(state),
    roomIds: bookRoomSelectors.getSearchResultIdsWithoutUnbookable(state),
    suggestedRoomIds: bookRoomSelectors.getSuggestedRoomIds(state),
    hasMoreTimelineData: bookRoomSelectors.hasMoreTimelineData(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    filters: bookRoomSelectors.getFilters(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        initTimeline: bookRoomActions.initTimeline,
        fetchTimeline: bookRoomActions.fetchTimeline,
        addTimelineRooms: bookRoomActions.addTimelineRooms,
        fetchRoomSuggestions: bookRoomActions.fetchRoomSuggestions,
      },
      dispatch
    ),
  })
)(BookingTimeline);
