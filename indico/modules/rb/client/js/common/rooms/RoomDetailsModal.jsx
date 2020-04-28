// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import qs from 'qs';
import moment from 'moment';
import React from 'react';
import {push as pushRoute} from 'connected-react-router';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import Overridable from 'react-overridable';
import {Button, Grid, Icon, Modal, Header, Message, List, Segment, Popup} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import {IndicoPropTypes, Markdown, Responsive, useResponsive} from 'indico/react/util';
import {serializeDate} from 'indico/utils/date';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import RoomStats from './RoomStats';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import * as roomsSelectors from './selectors';
import * as globalActions from '../../actions';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import {actions as calendarActions} from '../../modules/calendar';
import {actions as filtersActions} from '../../common/filters';
import {actions as bookingsActions} from '../../common/bookings';
import RoomEditModal from './edit/RoomEditModal';

import './RoomDetailsModal.module.scss';

class RoomDetailsModal extends React.Component {
  static propTypes = {
    room: PropTypes.object.isRequired,
    availability: PropTypes.array.isRequired,
    attributes: PropTypes.array.isRequired,
    onClose: PropTypes.func.isRequired,
    promptDatesOnBook: PropTypes.bool,
    title: IndicoPropTypes.i18n,
    gotoAllBookings: PropTypes.func.isRequired,
    actions: PropTypes.exact({
      openBookRoom: PropTypes.func.isRequired,
      openBookingForm: PropTypes.func.isRequired,
      openBookingDetails: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    promptDatesOnBook: false,
    title: <Translate>Room Details</Translate>,
  };

  state = {
    roomEditVisible: false,
  };

  showRoomEditModal = () => {
    this.setState({roomEditVisible: true});
  };

  handleCloseRoomEditModal = () => {
    this.setState({roomEditVisible: false});
  };

  handleCloseModal = () => {
    const {onClose} = this.props;
    onClose();
  };

  render() {
    const {
      room,
      availability,
      attributes,
      promptDatesOnBook,
      title,
      gotoAllBookings,
      actions: {openBookRoom, openBookingForm, openBookingDetails},
    } = this.props;
    const {roomEditVisible} = this.state;
    if (roomEditVisible) {
      return <RoomEditModal roomId={room.id} onClose={this.handleCloseRoomEditModal} />;
    }
    return (
      <Modal onClose={this.handleCloseModal} size="large" closeIcon open>
        <Modal.Header styleName="room-details-header">
          {title}
          <Responsive.Tablet andLarger>
            {room.canUserEdit && <Button icon="pencil" circular onClick={this.showRoomEditModal} />}
          </Responsive.Tablet>
        </Modal.Header>
        <Modal.Content>
          <RoomDetails
            room={room}
            attributes={attributes}
            availability={availability}
            bookRoom={promptDatesOnBook ? openBookRoom : openBookingForm}
            gotoAllBookings={gotoAllBookings}
            onClickReservation={openBookingDetails}
          />
        </Modal.Content>
      </Modal>
    );
  }
}

export default connect(
  (state, {roomId}) => ({
    room: roomsSelectors.getRoom(state, {roomId}),
    availability: roomsSelectors.getAvailability(state, {roomId}),
    attributes: roomsSelectors.getAttributes(state, {roomId}),
  }),
  dispatch => ({
    gotoAllBookings(roomId, bookingsPath) {
      dispatch(globalActions.resetPageState('calendar'));
      dispatch(filtersActions.setFilterParameter('calendar', 'text', `#${roomId}`));
      dispatch(calendarActions.setDate(serializeDate(moment().startOf('month'))));
      dispatch(calendarActions.setMode('months'));
      dispatch(pushRoute(bookingsPath));
    },
    actions: bindActionCreators(
      {
        openBookRoom: bookRoomActions.openBookRoom,
        openBookingForm: bookRoomActions.openBookingForm,
        openBookingDetails: bookingsActions.openBookingDetails,
      },
      dispatch
    ),
  })
)(Overridable.component('RoomDetailsModal', RoomDetailsModal));

const _getLegendLabels = availability => {
  const occurrenceTypes = availability.reduce(
    (types, day) => _.union(types, getOccurrenceTypes(day)),
    []
  );
  return transformToLegendLabels(occurrenceTypes);
};

function RoomDetails({
  bookRoom,
  room,
  availability,
  attributes,
  gotoAllBookings,
  onClickReservation,
}) {
  const legendLabels = _getLegendLabels(availability);
  const rowSerializer = ({
    bookings,
    preBookings,
    nonbookablePeriods,
    unbookableHours,
    blockings,
    overridableBlockings,
    day,
  }) => ({
    availability: {
      bookings: bookings || [],
      preBookings: preBookings || [],
      nonbookablePeriods: nonbookablePeriods || [],
      unbookableHours: unbookableHours || [],
      blockings: blockings || [],
      overridableBlockings: overridableBlockings || [],
    },
    label: moment(day).format('L'),
    key: day,
    room,
  });

  const params = {
    text: `#${room.id}`,
    mode: 'months',
    date: serializeDate(moment().startOf('month')),
  };
  const bookingsPath = `calendar?${qs.stringify(params)}`;
  const {isPhone} = useResponsive();

  return (
    <div styleName="room-details">
      <Grid stackable columns={2}>
        <Grid.Column>
          <div>
            <RoomBasicDetails room={room} />
            <Overridable id="RoomDetails.infoBoxes" room={room}>
              <>
                <RoomAvailabilityBox room={room} />
                <RoomCommentsBox room={room} />
                <RoomKeyLocation room={room} />
                <RoomCustomAttributesBox attributes={attributes} />
              </>
            </Overridable>
          </div>
        </Grid.Column>
        <Grid.Column>
          <Header className="legend-header">
            <Translate>Usage</Translate>
            {!isPhone && (
              <Popup
                trigger={<Icon name="info circle" className="legend-info-icon" />}
                content={<TimelineLegend labels={legendLabels} compact />}
              />
            )}
            <Button
              as="a"
              href={bookingsPath}
              basic
              size="tiny"
              compact
              color="blue"
              styleName="all-bookings"
              onClick={evt => {
                if (evt.button === 0) {
                  evt.preventDefault();
                  gotoAllBookings(room.id, bookingsPath);
                }
              }}
            >
              <Translate>See all bookings</Translate>
            </Button>
          </Header>
          <Responsive.Tablet andLarger>
            <DailyTimelineContent
              rows={availability.map(rowSerializer)}
              onClickReservation={onClickReservation}
            />
          </Responsive.Tablet>
          <RoomStats roomId={room.id} />
          {(room.canUserBook || room.canUserPrebook) && (
            <>
              <Message attached info>
                <Icon name="info" />
                <Translate>Would you like to use this space?</Translate>
              </Message>
              <Segment attached="bottom">
                {room.canUserBook && (
                  <Button color="green" onClick={() => bookRoom(room.id, {isPrebooking: false})}>
                    <Icon name="check circle" />
                    <Translate>Start booking</Translate>
                  </Button>
                )}
                {room.canUserPrebook && (
                  <Button color="orange" onClick={() => bookRoom(room.id, {isPrebooking: true})}>
                    <Icon name="check circle" />
                    <Translate>Start pre-booking</Translate>
                  </Button>
                )}
              </Segment>
            </>
          )}
        </Grid.Column>
      </Grid>
    </div>
  );
}

RoomDetails.propTypes = {
  bookRoom: PropTypes.func.isRequired,
  room: PropTypes.object.isRequired,
  availability: PropTypes.array.isRequired,
  attributes: PropTypes.array.isRequired,
  gotoAllBookings: PropTypes.func.isRequired,
  onClickReservation: PropTypes.func.isRequired,
};

function RoomAvailabilityBox({room}) {
  if (room.canUserBook || room.canUserPrebook) {
    return (
      <Message
        positive
        styleName="message-icon"
        icon="unlock"
        content={
          <>
            <p>
              {room.isPublic ? (
                <Translate>Anyone can book this space.</Translate>
              ) : (
                <Translate>You can book this space.</Translate>
              )}
            </p>
            {room.maxAdvanceDays && (
              <p>
                <Translate>
                  Max. <Param name="max_advance_days" value={room.maxAdvanceDays} /> days in advance
                </Translate>
              </p>
            )}
          </>
        }
      />
    );
  } else if (!room.isReservable) {
    return (
      <Message
        negative
        styleName="message-icon"
        icon="exclamation triangle"
        content={Translate.string('This space cannot be booked at the moment.')}
      />
    );
  } else {
    return (
      <Message
        negative
        styleName="message-icon"
        icon="lock"
        content={Translate.string('You are not authorized to book this space.')}
      />
    );
  }
}

RoomAvailabilityBox.propTypes = {
  room: PropTypes.object.isRequired,
};

function RoomCommentsBox({room}) {
  return (
    room.comments && (
      <Message styleName="message-icon" icon info>
        <Icon name="info" />
        <Message.Content>
          <Markdown source={room.comments} targetBlank />
        </Message.Content>
      </Message>
    )
  );
}

RoomCommentsBox.propTypes = {
  room: PropTypes.object.isRequired,
};

function RoomCustomAttributesBox({attributes}) {
  return (
    !!attributes.length && (
      <Message>
        <List>
          {attributes.map(({title, value}) => (
            <List.Item key={title}>
              <span styleName="attribute-title">
                <strong>{title}</strong>
              </span>
              <span>{value}</span>
            </List.Item>
          ))}
        </List>
      </Message>
    )
  );
}

RoomCustomAttributesBox.propTypes = {
  attributes: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
    })
  ).isRequired,
};
