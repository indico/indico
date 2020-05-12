// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Button} from 'semantic-ui-react';
import {connect} from 'react-redux';
import Overridable from 'react-overridable';

import {Translate} from 'indico/react/i18n';
import {isBookingStartDateValid, getMinimumBookingStartTime, createDT} from 'indico/utils/date';
import {FilterBarController, FilterDropdownFactory} from '../../common/filters/FilterBar';

import RecurrenceForm from './filters/RecurrenceForm';
import DateForm from './filters/DateForm';
import TimeForm from './filters/TimeForm';

import {renderRecurrence} from '../../util';
import dateRenderer from './filters/DateRenderer';
import timeRenderer from './filters/TimeRenderer';
import {actions as filtersActions} from '../../common/filters';
import {selectors as userSelectors} from '../../common/user';
import {selectors as configSelectors} from '../../common/config';
import * as bookRoomSelectors from './selectors';

class BookingFilterBar extends React.Component {
  static propTypes = {
    dayBased: PropTypes.bool,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    filters: PropTypes.shape({
      recurrence: PropTypes.shape({
        number: PropTypes.number,
        type: PropTypes.string,
        interval: PropTypes.string,
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

    return (
      <Button.Group size="small">
        <Button icon="calendar alternate outline" as="div" disabled />
        <FilterBarController>
          <Overridable id="BookingFilterBar.recurrence">
            <FilterDropdownFactory
              name="recurrence"
              title={<Translate>Recurrence</Translate>}
              form={(fieldValues, setParentField) => (
                <RecurrenceForm setParentField={setParentField} {...fieldValues} />
              )}
              setGlobalState={({type, number, interval}) => {
                setFilterParameter('recurrence', {type, number, interval});
              }}
              initialValues={recurrence}
              defaults={{
                type: 'single',
                number: 1,
                interval: 'week',
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
                disabledDate={dt =>
                  !isBookingStartDateValid(dt, isAdminOverrideEnabled, bookingGracePeriod)
                }
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
