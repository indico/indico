// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {getMinimumBookingStartTime, createDT, getBookingRangeMinDate} from 'indico/utils/date';

import {selectors as configSelectors} from '../../common/config';
import {actions as filtersActions} from '../../common/filters';
import {FilterBarController, FilterDropdownFactory} from '../../common/filters/FilterBar';
import {selectors as userSelectors} from '../../common/user';
import {renderRecurrence} from '../../util';

import DateForm from './filters/DateForm';
import dateRenderer from './filters/DateRenderer';
import RecurrenceForm from './filters/RecurrenceForm';
import TimeForm from './filters/TimeForm';
import timeRenderer from './filters/TimeRenderer';
import * as bookRoomSelectors from './selectors';

import './BookingFilterBar.module.scss';

class BookingFilterBar extends React.Component {
  static propTypes = {
    dayBased: PropTypes.bool,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    filters: PropTypes.shape({
      recurrence: PropTypes.shape({
        number: PropTypes.number,
        type: PropTypes.string,
        interval: PropTypes.string,
        weekdays: PropTypes.arrayOf(PropTypes.string),
      }).isRequired,
      dates: PropTypes.shape({
        startDate: PropTypes.string,
        endDate: PropTypes.string,
      }).isRequired,
      timeSlot: PropTypes.shape({
        startTime: PropTypes.string,
        endTime: PropTypes.string,
      }),
    }).isRequired,
    actions: PropTypes.shape({
      setFilterParameter: PropTypes.func,
    }).isRequired,
    bookingGracePeriod: PropTypes.number,
  };

  static defaultProps = {
    dayBased: false,
    bookingGracePeriod: null,
  };

  render() {
    const {
      dayBased,
      filters: {recurrence, dates, timeSlot},
      actions: {setFilterParameter},
      isAdminOverrideEnabled,
      bookingGracePeriod,
    } = this.props;
    const minTime = getMinimumBookingStartTime(
      createDT(dates.startDate, '00:00'),
      isAdminOverrideEnabled,
      bookingGracePeriod
    );
    const minDate = getBookingRangeMinDate(isAdminOverrideEnabled, bookingGracePeriod);

    return (
      <Button.Group size="small" styleName="recurrence-bar">
        <Button icon="calendar alternate outline" as="div" disabled />
        <FilterBarController>
          <Overridable id="BookingFilterBar.recurrence">
            <FilterDropdownFactory
              name="recurrence"
              title={<Translate>Recurrence</Translate>}
              form={(fieldValues, setParentField) => (
                <RecurrenceForm setParentField={setParentField} {...fieldValues} />
              )}
              setGlobalState={({type, number, interval, weekdays}) => {
                setFilterParameter('recurrence', {type, number, interval, weekdays});
              }}
              initialValues={recurrence}
              defaults={{
                type: 'single',
                number: 1,
                interval: 'week',
                weekdays: [],
              }}
              renderValue={renderRecurrence}
            />
          </Overridable>
          <FilterDropdownFactory
            name="dates"
            title={<Translate>Date</Translate>}
            form={(fieldValues, setParentField) => (
              <DateForm
                setParentField={setParentField}
                isRange={recurrence.type !== 'single'}
                minDate={minDate}
                {...dates}
              />
            )}
            setGlobalState={setFilterParameter.bind(undefined, 'dates')}
            initialValues={dates}
            renderValue={dateRenderer}
          />
          {!dayBased && (
            <FilterDropdownFactory
              name="timeSlot"
              title={<Translate>Time</Translate>}
              form={(fieldValues, setParentField) => (
                <TimeForm setParentField={setParentField} minTime={minTime} {...fieldValues} />
              )}
              setGlobalState={setFilterParameter.bind(undefined, 'timeSlot')}
              initialValues={timeSlot}
              renderValue={timeRenderer}
            />
          )}
        </FilterBarController>
      </Button.Group>
    );
  }
}

export default connect(
  state => ({
    filters: bookRoomSelectors.getFilters(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    bookingGracePeriod: configSelectors.getBookingGracePeriod(state),
  }),
  dispatch => ({
    actions: {
      setFilterParameter: (param, value) => {
        dispatch(filtersActions.setFilterParameter('bookRoom', param, value));
      },
    },
  })
)(Overridable.component('BookingFilterBar', BookingFilterBar));
