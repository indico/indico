// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Header, Icon, List, Message, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import OccurrencesCounter from './OccurrencesCounter';
import * as bookingsSelectors from './selectors';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';

import './BookingEditCalendar.module.scss';

class BookingEditCalendar extends React.Component {
  static propTypes = {
    booking: PropTypes.object.isRequired,
    numberOfBookingOccurrences: PropTypes.number.isRequired,
    numberOfCandidates: PropTypes.number,
    willBookingSplit: PropTypes.bool.isRequired,
    calendars: PropTypes.object.isRequired,
    isLoading: PropTypes.bool,
  };

  static defaultProps = {
    numberOfCandidates: 0,
    isLoading: false,
  };

  getLegendLabels = calendars => {
    const occurrenceTypes = calendars.reduce((accumTypes, data) => {
      const calendarTypes = data.reduce((types, {availability}) => {
        return _.union(types, getOccurrenceTypes(availability));
      }, []);
      return _.union(accumTypes, calendarTypes);
    }, []);
    return transformToLegendLabels(occurrenceTypes);
  };

  serializeRow = data => {
    const {
      booking: {room},
    } = this.props;
    return day => ({
      availability: {
        bookings: data.bookings[day] || [],
        cancellations: data.cancellations[day] || [],
        rejections: data.rejections[day] || [],
        other: data.other[day] || [],
        candidates: (data.candidates[day] || []).map(candidate => ({
          ...candidate,
          bookable: false,
        })),
        conflictingCandidates: (data.conflictingCandidates[day] || []).map(candidate => ({
          ...candidate,
          bookable: false,
        })),
        conflicts: data.conflicts[day] || [],
        pendingCancellations: data.pendingCancellations[day] || [],
        blockings: data.blockings[day] || [],
        overridableBlockings: data.overridableBlockings[day] || [],
        nonbookablePeriods: data.nonbookablePeriods[day] || [],
        unbookableHours: data.unbookableHours || [],
      },
      label: serializeDate(day, 'L'),
      key: day,
      room,
    });
  };

  getCalendarData = calendar => {
    const {isLoading} = this.props;
    const {dateRange, data} = calendar;
    return isLoading ? [] : dateRange.map(this.serializeRow(data));
  };

  renderNumberOfOccurrences = () => {
    const {
      calendars: {
        currentBooking: {
          data: {bookings, pendingCancellations, cancellations, rejections},
        },
      },
      numberOfBookingOccurrences,
      numberOfCandidates,
      willBookingSplit,
    } = this.props;
    const numBookingPastOccurrences = willBookingSplit
      ? Object.keys(bookings).length -
        Object.keys(pendingCancellations).length -
        Object.keys(cancellations || {}).length -
        Object.keys(rejections || {}).length
      : null;

    return (
      <OccurrencesCounter
        bookingsCount={numberOfBookingOccurrences}
        newBookingsCount={numberOfCandidates}
        pastBookingsCount={numBookingPastOccurrences}
      />
    );
  };

  render() {
    const {
      willBookingSplit,
      calendars: {currentBooking, newBooking},
      isLoading,
    } = this.props;
    const currentBookingRows = this.getCalendarData(currentBooking);
    const newBookingRows = newBooking ? this.getCalendarData(newBooking) : [];
    const legendLabels = this.getLegendLabels([currentBookingRows, newBookingRows]);

    return (
      <div styleName="booking-calendar">
        <Header className="legend-header">
          <span>
            <Translate>Occurrences</Translate>
          </span>
          <Popup
            trigger={<Icon name="info circle" className="legend-info-icon" />}
            position="right center"
            content={<TimelineLegend labels={legendLabels} compact />}
          />
          {this.renderNumberOfOccurrences()}
        </Header>
        {willBookingSplit && (
          <Message styleName="ongoing-booking-explanation" color="green" icon>
            <Icon name="code branch" />
            <Message.Content>
              <Translate>Your booking has already started and will be split into:</Translate>
              <List bulleted>
                <List.Item>
                  <Translate>the original booking, which will be shortened;</Translate>
                </List.Item>
                <List.Item>
                  <Translate>
                    a new booking, which will take into account the updated time information.
                  </Translate>
                </List.Item>
              </List>
            </Message.Content>
          </Message>
        )}
        <div styleName="calendars">
          <div styleName="original-booking">
            <DailyTimelineContent
              rows={currentBookingRows}
              renderHeader={
                newBooking
                  ? () => (
                      <Header as="h3" color="orange" styleName="original-booking-header">
                        <Translate>Original booking</Translate>
                      </Header>
                    )
                  : null
              }
              isLoading={isLoading}
              fixedHeight={currentBooking.dateRange.length > 0 ? '100%' : null}
            />
          </div>
          {newBooking && (
            <div styleName="new-booking">
              <DailyTimelineContent
                rows={newBookingRows}
                renderHeader={() => {
                  return (
                    <Header as="h3" color="green" styleName="new-booking-header">
                      {willBookingSplit ? (
                        <Translate>New booking</Translate>
                      ) : (
                        <Translate>Booking after changes</Translate>
                      )}
                    </Header>
                  );
                }}
                fixedHeight={newBooking.dateRange.length > 0 ? '100%' : null}
              />
            </div>
          )}
        </div>
      </div>
    );
  }
}

export default connect((state, {booking: {id}}) => ({
  numberOfBookingOccurrences: bookingsSelectors.getNumberOfBookingOccurrences(state, {
    bookingId: id,
  }),
}))(BookingEditCalendar);
