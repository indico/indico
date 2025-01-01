// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Modal, Icon, Popup} from 'semantic-ui-react';

import {getWeekday, serializeDate} from 'indico/utils/date';

import {actions as bookRoomActions, selectors as bookRoomSelectors} from '../../modules/bookRoom';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';

import DailyTimelineContent from './DailyTimelineContent';
import TimelineLegend from './TimelineLegend';

import './SingleRoomTimelineModal.module.scss';
import '../../components/WeekdayInformation.module.scss';

const _getRowSerializer = (day, room) => {
  return ({
    bookings,
    preBookings,
    candidates,
    conflictingCandidates,
    nonbookablePeriods,
    unbookableHours,
    blockings,
    overridableBlockings,
    conflicts,
    preConflicts,
    concurrentPreBookings,
  }) => ({
    availability: {
      candidates: (candidates[day] || []).map(candidate => ({...candidate, bookable: false})) || [],
      conflictingCandidates:
        (conflictingCandidates[day] || []).map(candidate => ({...candidate, bookable: false})) ||
        [],
      preBookings: preBookings[day] || [],
      bookings: bookings[day] || [],
      conflicts: conflicts[day] || [],
      preConflicts: preConflicts[day] || [],
      nonbookablePeriods: nonbookablePeriods[day] || [],
      unbookableHours: unbookableHours[getWeekday(day)],
      blockings: blockings[day] || [],
      overridableBlockings: overridableBlockings[day] || [],
      concurrentPreBookings: concurrentPreBookings[day] || [],
    },
    label: (
      <>
        <span styleName="weekday">{moment(day).format('ddd')}</span> {serializeDate(day, 'L')}
      </>
    ),
    key: day,
    room,
  });
};

const _getLegendLabels = availability => {
  const occurrenceTypes = getOccurrenceTypes(availability);
  return transformToLegendLabels(occurrenceTypes);
};

const _SingleRoomTimelineContent = props => {
  const {
    availability,
    availabilityLoading,
    room,
    title,
    filters,
    roomAvailability,
    actions: {fetchAvailability},
  } = props;
  useEffect(() => {
    if (_.isEmpty(roomAvailability)) {
      fetchAvailability(room, filters);
    }
  }, [fetchAvailability, filters, room, roomAvailability]);

  const isLoaded = !_.isEmpty(availability) && !availabilityLoading;
  const dateRange = isLoaded ? availability.dateRange : [];
  const rows = isLoaded ? dateRange.map(day => _getRowSerializer(day, room)(availability)) : [];
  const legendLabels = isLoaded ? _getLegendLabels(availability) : [];
  return (
    <>
      <Modal.Header className="legend-header">
        {title}
        <Popup
          trigger={<Icon name="info circle" className="legend-info-icon" />}
          content={<TimelineLegend labels={legendLabels} compact />}
        />
      </Modal.Header>
      <Modal.Content>
        <DailyTimelineContent
          rows={rows}
          fixedHeight={rows.length > 1 ? '70vh' : null}
          isLoading={!isLoaded}
        />
      </Modal.Content>
    </>
  );
};

_SingleRoomTimelineContent.propTypes = {
  room: PropTypes.object.isRequired,
  availability: PropTypes.object,
  availabilityLoading: PropTypes.bool.isRequired,
  filters: PropTypes.object.isRequired,
  roomAvailability: PropTypes.object,
  title: PropTypes.node.isRequired,
  actions: PropTypes.exact({
    fetchAvailability: PropTypes.func.isRequired,
  }).isRequired,
};

_SingleRoomTimelineContent.defaultProps = {
  availability: {},
  roomAvailability: {},
};

const SingleRoomTimelineContent = connect(
  state => ({
    filters: bookRoomSelectors.getFilters(state),
    availability: bookRoomSelectors.getBookingFormAvailability(state),
    availabilityLoading: bookRoomSelectors.isFetchingFormTimeline(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchAvailability: bookRoomActions.fetchBookingAvailability,
      },
      dispatch
    ),
  })
)(React.memo(_SingleRoomTimelineContent));

/**
 * Timeline modal for a single room
 *
 * @param {Boolean} props.open - Whether the modal should be visible.
 * @param {String} props.title - Modal title.
 * @param {Function} props.onClose - Function to execute when closing the modal.
 * @param {Object} props.roomAvailability - Room availability if it was previously
 * fetched, otherwise it'll be fetched here.
 * @param {Object} props.room - Room whose timeline will be displayed.
 */
const SingleRoomTimelineModal = props => {
  const {open, title, onClose, roomAvailability, room} = props;
  return (
    <Modal open={open} onClose={onClose} size="large" closeIcon>
      <SingleRoomTimelineContent
        room={room}
        roomAvailability={roomAvailability}
        title={title || room.name}
      />
    </Modal>
  );
};

SingleRoomTimelineModal.propTypes = {
  open: PropTypes.bool,
  title: PropTypes.node,
  onClose: PropTypes.func,
  roomAvailability: PropTypes.object,
  room: PropTypes.object.isRequired,
};

SingleRoomTimelineModal.defaultProps = {
  open: false,
  title: '',
  onClose: () => {},
  roomAvailability: {},
};

export default SingleRoomTimelineModal;
