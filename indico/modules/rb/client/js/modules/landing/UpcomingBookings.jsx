// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Header, List} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';

import {actions as bookingActions} from '../../common/bookings';
import SpriteImage from '../../components/SpriteImage';

import './UpcomingBookings.module.scss';

/**
 * A widget that shows the user a list of their upcoming bookings
 */
class UpcomingBookings extends React.PureComponent {
  static propTypes = {
    /** The list of booking objects */
    bookings: PropTypes.arrayOf(PropTypes.object).isRequired,
    actions: PropTypes.exact({
      openBookingDetails: PropTypes.func,
    }).isRequired,
  };

  renderCard({reservation: {room, id: resvId, bookingReason, isAccepted}, startDt}) {
    const mStartDT = toMoment(startDt);
    const {actions} = this.props;
    const fullDate = mStartDT.format('ddd D MMM YYYY, LT');

    return (
      <List.Item key={`${resvId}-${startDt}`} styleName="upcoming-bookings-item">
        <List.Content>
          <div styleName="upcoming-item-img-container">
            <SpriteImage
              pos={room.spritePosition}
              width="100%"
              height="100px"
              styles={{margin: 'auto'}}
            />
            <List.Header as="h3" styleName="upcoming-item-room-notch">
              <span styleName="upcoming-item-room-name">{room.name}</span>
            </List.Header>
          </div>
          <List.Description>
            <time dateTime={startDt}>{fullDate}</time>
            {!isAccepted && (
              <span styleName="pending-status">
                <Translate>Pending confirmation</Translate>
              </span>
            )}
            <p styleName="booking-reason">{bookingReason}</p>
          </List.Description>
        </List.Content>
        <button
          type="button"
          styleName="details-button"
          onClick={() => actions.openBookingDetails(resvId)}
        >
          <span styleName="details-button-text">
            <Translate>View booking details</Translate>: {room.name}, {fullDate}
          </span>
        </button>
      </List.Item>
    );
  }

  render() {
    const {bookings} = this.props;
    return (
      <div>
        <Header as="h3">
          <Translate>Your bookings</Translate>
        </Header>
        <List divided horizontal relaxed styleName="upcoming-bookings-list">
          {bookings.map(booking => this.renderCard(booking))}
        </List>
      </div>
    );
  }
}

export default connect(null, dispatch => ({
  actions: bindActionCreators(
    {
      openBookingDetails: bookingActions.openBookingDetails,
    },
    dispatch
  ),
}))(UpcomingBookings);
