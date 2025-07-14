// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import LazyScroll from 'redux-lazy-scroll';
import {
  Button,
  Card,
  Confirm,
  Divider,
  Header,
  Icon,
  Label,
  Message,
  Popup,
} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import {actions as bookingsActions} from '../../common/bookings';
import {actions as linkingActions, selectors as linkingSelectors} from '../../common/linking';
import {selectors as userSelectors} from '../../common/user';
import CardPlaceholder from '../../components/CardPlaceholder';

import * as calendarActions from './actions';
import * as calendarSelectors from './selectors';

import './CalendarListView.module.scss';

const ACTIVE_BOOKINGS_LIMIT = 40;
const BOOKING_LINKING_RANGE_INCREASE = 7;

class CalendarListView extends React.Component {
  static propTypes = {
    bookings: PropTypes.object.isRequired,
    rowsLeft: PropTypes.number.isRequired,
    isFetchingActiveBookings: PropTypes.bool.isRequired,
    roomFilters: PropTypes.object.isRequired,
    calendarFilters: PropTypes.object.isRequired,
    datePicker: PropTypes.object.isRequired,
    linkData: PropTypes.object,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    bookingLinkingDisplayRange: PropTypes.exact({
      earlier: PropTypes.number.isRequired,
      later: PropTypes.number.isRequired,
    }).isRequired,
    actions: PropTypes.exact({
      openBookingDetails: PropTypes.func.isRequired,
      linkBookingOccurrence: PropTypes.func.isRequired,
      fetchActiveBookings: PropTypes.func.isRequired,
      clearActiveBookings: PropTypes.func.isRequired,
      addEarlier: PropTypes.func.isRequired,
      addLater: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    linkData: null,
  };

  state = {
    linkingConfirm: null,
  };

  componentDidMount() {
    const {
      actions: {fetchActiveBookings},
    } = this.props;
    fetchActiveBookings(ACTIVE_BOOKINGS_LIMIT);
  }

  componentDidUpdate(prevProps) {
    const {
      datePicker: {selectedDate: prevDate, mode: prevMode},
      roomFilters: prevRoomFilters,
      calendarFilters: prevCalendarFilters,
      bookingLinkingDisplayRange: prevBookingLinkingDisplayRange,
      linkData: prevLinkData,
      isAdminOverrideEnabled: prevIsAdminOverrideEnabled,
    } = prevProps;
    const {
      datePicker: {selectedDate, mode},
      roomFilters,
      calendarFilters,
      bookingLinkingDisplayRange,
      linkData,
      isAdminOverrideEnabled,
    } = this.props;

    const roomFiltersChanged = !_.isEqual(prevRoomFilters, roomFilters);
    const calendarFiltersChanged = !_.isEqual(prevCalendarFilters, calendarFilters);
    const bookingDisplayFiltersChanged = !_.isEqual(
      prevBookingLinkingDisplayRange,
      bookingLinkingDisplayRange
    );
    const linkDataChanged = !_.isEqual(prevLinkData, linkData);
    const adminOverrideChanged = prevIsAdminOverrideEnabled !== isAdminOverrideEnabled;
    if (
      prevDate !== selectedDate ||
      mode !== prevMode ||
      roomFiltersChanged ||
      calendarFiltersChanged ||
      bookingDisplayFiltersChanged ||
      linkDataChanged ||
      (linkData && adminOverrideChanged)
    ) {
      this.refetchActiveBookings(roomFiltersChanged);
    }
  }

  componentWillUnmount() {
    const {
      actions: {clearActiveBookings},
    } = this.props;
    clearActiveBookings();
  }

  refetchActiveBookings(roomFiltersChanged) {
    const {
      actions: {fetchActiveBookings, clearActiveBookings},
    } = this.props;
    clearActiveBookings();
    fetchActiveBookings(ACTIVE_BOOKINGS_LIMIT, roomFiltersChanged);
  }

  fetchMoreBookings = () => {
    const {
      actions: {fetchActiveBookings},
      linkData,
    } = this.props;
    if (!linkData) {
      fetchActiveBookings(ACTIVE_BOOKINGS_LIMIT, false);
    }
  };

  renderDayBookings = (day, bookings) => {
    if (!bookings.length) {
      return null;
    }

    return (
      <div styleName="day-cards" key={day}>
        <Header styleName="day-cards-header" dividing>
          <Icon name="calendar outline" />
          {moment(day, 'YYYY-MM-DD').format('dddd, LL')}
        </Header>
        <Card.Group itemsPerRow={4} stackable styleName="day-cards-container">
          {bookings.map(booking => this.renderBooking(booking, day))}
        </Card.Group>
        <Divider hidden />
      </div>
    );
  };

  renderLink = (booking, day) => {
    const {
      linkData,
      isAdminOverrideEnabled,
      actions: {linkBookingOccurrence},
    } = this.props;
    if (!linkData) {
      return;
    }
    const {linkingConfirm} = this.state;
    const {reservation} = booking;
    if (booking.linkId) {
      return;
    }
    const linkBtn = (
      <Button
        icon={<Icon name="linkify" />}
        primary
        size="small"
        circular
        onClick={e => {
          e.stopPropagation();
          this.setState({
            linkingConfirm: {reservationId: reservation.id, day, linkId: linkData.id},
          });
        }}
      />
    );
    return (
      <>
        <Confirm
          size="mini"
          header={Translate.string('Link event')}
          open={
            linkingConfirm &&
            (linkingConfirm.reservationId === reservation.id && linkingConfirm.day === day)
          }
          content={Translate.string('Are you sure you want to link this event?')}
          closeOnDimmerClick
          closeOnEscape
          onClose={e => {
            e.stopPropagation();
            this.setState({linkingConfirm: null});
          }}
          onConfirm={e => {
            e.stopPropagation();
            this.setState({linkingConfirm: null});
            linkBookingOccurrence(reservation.id, day, linkData.id, isAdminOverrideEnabled, () =>
              this.refetchActiveBookings(false)
            );
          }}
          onCancel={e => {
            e.stopPropagation();
            this.setState({linkingConfirm: null});
          }}
          onOpen={e => e.stopPropagation()}
          cancelButton={<Button content={Translate.string('Cancel')} />}
          confirmButton={
            <Button content={Translate.string('Link', 'Link a booking to an event (verb)')} />
          }
          closeIcon
        />
        <div style={{position: 'absolute', top: '35%', right: '5px'}}>
          <Popup trigger={linkBtn} position="bottom center">
            <Translate>
              Link to <Param name="bookedFor" wrapper={<strong />} value={linkData.title} />
            </Translate>
          </Popup>
        </div>
      </>
    );
  };

  renderBooking = (booking, day) => {
    const {
      linkData,
      actions: {openBookingDetails},
    } = this.props;
    const {reservation} = booking;
    const {room, isAccepted} = reservation;
    const key = `${reservation.id}-${booking.startDt}-${booking.endDt}`;
    let datesMatch = false;
    if (linkData) {
      const boundaries = [moment(linkData.startDt), moment(linkData.endDt)];
      datesMatch =
        moment(booking.startDt).isBetween(...boundaries, undefined, '[]') &&
        moment(booking.endDt).isBetween(...boundaries, undefined, '[]');
    }
    const nonOverlapping = !!linkData && !datesMatch;
    const startTime = moment(booking.startDt, 'YYYY-MM-DD HH:mm').format('LT');
    const endTime = moment(booking.endDt, 'YYYY-MM-DD HH:mm').format('LT');
    const isLinked = !!linkData && !!booking.linkId;
    return (
      <Card
        styleName={`booking-card ${toClasses({
          'already-linked': isLinked,
        })}`}
        key={key}
        onClick={() => openBookingDetails(reservation.id)}
      >
        <Card.Content>
          <Card.Header>
            {!isAccepted && (
              <Popup
                trigger={<Label color="yellow" icon="clock" corner="right" size="tiny" />}
                content={Translate.string('This booking is pending confirmation by the room owner')}
                position="right center"
              />
            )}
            <TooltipIfTruncated>
              <div styleName="booking-card-header">{room.fullName}</div>
            </TooltipIfTruncated>
          </Card.Header>
          <Card.Meta>
            {startTime} - {endTime}
          </Card.Meta>
          <Card.Description>{reservation.bookingReason}</Card.Description>
        </Card.Content>
        <Card.Content extra>
          <TooltipIfTruncated>
            <div styleName="booking-booked-for">
              <Translate>
                Booked for <Param name="bookedFor" value={reservation.bookedForName} />
              </Translate>
            </div>
          </TooltipIfTruncated>
          {isLinked && (
            <TooltipIfTruncated>
              <div styleName="booking-booked-for">
                <Translate>Already linked</Translate>
              </div>
            </TooltipIfTruncated>
          )}
          {nonOverlapping && (
            <TooltipIfTruncated>
              <div styleName="booking-booked-for">
                <Translate>Outside of the event schedule</Translate>
              </div>
            </TooltipIfTruncated>
          )}
        </Card.Content>
        {this.renderLink(booking, day)}
      </Card>
    );
  };

  render() {
    const {
      bookings,
      rowsLeft,
      isFetchingActiveBookings,
      linkData,
      bookingLinkingDisplayRange: {earlier, later},
      actions: {addEarlier, addLater},
    } = this.props;
    const sortedEntries = _.sortBy(Object.entries(bookings), item => item[0]);
    const hasData = Object.keys(sortedEntries).length !== 0;

    const linkingShowEarlier = (
      <Message info>
        {earlier ? (
          <PluralTranslate count={earlier}>
            <Singular>
              Showing bookings up to <Param name="days" value={earlier} /> day before the event.
            </Singular>
            <Plural>
              Showing bookings up to <Param name="days" value={earlier} /> days before the event.
            </Plural>
          </PluralTranslate>
        ) : (
          <Translate>Showing bookings around the event dates.</Translate>
        )}{' '}
        <a
          href="#"
          onClick={evt => {
            evt.preventDefault();
            addEarlier(BOOKING_LINKING_RANGE_INCREASE);
          }}
        >
          <Translate>Load earlier bookings</Translate>
        </a>
      </Message>
    );

    const linkingShowLater = (
      <Message info>
        {later ? (
          <PluralTranslate count={later}>
            <Singular>
              Showing bookings up to <Param name="days" value={later} /> day after the event.
            </Singular>
            <Plural>
              Showing bookings up to <Param name="days" value={later} /> days after the event.
            </Plural>
          </PluralTranslate>
        ) : (
          <Translate>Showing bookings around the event dates.</Translate>
        )}{' '}
        <a
          href="#"
          onClick={evt => {
            evt.preventDefault();
            addLater(BOOKING_LINKING_RANGE_INCREASE);
          }}
        >
          <Translate>Load later bookings</Translate>
        </a>
      </Message>
    );

    return (
      <div styleName="active-bookings">
        {(isFetchingActiveBookings || hasData) && (
          <LazyScroll
            hasMore={rowsLeft > 0}
            loadMore={this.fetchMoreBookings}
            isFetching={isFetchingActiveBookings}
          >
            {linkData && linkingShowEarlier}
            {sortedEntries.map(bookingsData => this.renderDayBookings(...bookingsData))}
            {isFetchingActiveBookings && (
              <CardPlaceholder.Group
                count={ACTIVE_BOOKINGS_LIMIT}
                itemsPerRow={4}
                withImage={false}
              />
            )}
            {linkData && linkingShowLater}
          </LazyScroll>
        )}
        {!isFetchingActiveBookings && !hasData && (
          <>
            {linkData && linkingShowEarlier}
            <Message info>
              <Translate>There are no bookings matching the criteria.</Translate>
            </Message>
            {linkData && linkingShowLater}
          </>
        )}
      </div>
    );
  }
}

export default connect(
  state => ({
    bookings: calendarSelectors.getActiveBookings(state),
    rowsLeft: calendarSelectors.getNumberOfRowsLeft(state),
    isFetchingActiveBookings: calendarSelectors.isFetchingActiveBookings(state),
    roomFilters: calendarSelectors.getRoomFilters(state),
    calendarFilters: calendarSelectors.getCalendarFilters(state),
    datePicker: calendarSelectors.getDatePickerInfo(state),
    linkData: linkingSelectors.getLinkObject(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    bookingLinkingDisplayRange: linkingSelectors.getLinkingDisplayRange(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        openBookingDetails: bookingsActions.openBookingDetails,
        linkBookingOccurrence: bookingsActions.linkBookingOccurrence,
        fetchActiveBookings: calendarActions.fetchActiveBookings,
        clearActiveBookings: calendarActions.clearActiveBookings,
        addEarlier: linkingActions.addEarlier,
        addLater: linkingActions.addLater,
      },
      dispatch
    ),
  })
)(CalendarListView);
