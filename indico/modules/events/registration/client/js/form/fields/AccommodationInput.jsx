// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {DatePeriodField, FinalDatePeriod} from 'indico/react/components';
import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';

import {Choices, choiceShape} from './ChoicesSetup';

import '../../../styles/regform.module.scss';

export default function AccommodationInput({htmlName, disabled, choices, arrival, departure}) {
  // TODO: billable/price
  // TODO: places left
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const [value, setValue] = useState({
    choice: null,
    isNoAccommodation: false,
    arrivalDate: null,
    departureDate: null,
  });

  const [focusedDateField, setFocusedDateField] = useState(null);

  const arrivalDateFrom = toMoment(arrival.startDate, moment.HTML5_FMT.DATE);
  const arrivalDateTo = toMoment(arrival.endDate, moment.HTML5_FMT.DATE);
  const departureDateFrom = toMoment(departure.startDate, moment.HTML5_FMT.DATE);
  const departureDateTo = toMoment(departure.endDate, moment.HTML5_FMT.DATE);

  const makeHandleChange = choice => () => {
    setValue(prev => {
      const newValue = {...prev, choice: choice.id, isNoAccommodation: choice.isNoAccommodation};
      if (choice.isNoAccommodation) {
        newValue.arrivalDate = null;
        newValue.departureDate = null;
      }
      return newValue;
    });
  };

  const handleDateChange = ({startDate, endDate}) => {
    setValue(prev => ({...prev, arrivalDate: startDate, departureDate: endDate}));
  };

  const isDateDisabled = date => {
    // for the arrival date we allow selecting from the start date range, but for the
    // departure date we allow both ranges to avoid the highlighted range looking very
    // broken (disabled dates do not get any highlighting when included in the range)
    if (focusedDateField === 'startDate') {
      return !date.isBetween(arrivalDateFrom, arrivalDateTo, 'day', '[]');
    }
    return !date.isBetween(arrivalDateFrom, departureDateTo, 'day', '[]');
  };

  // calculate minimum days so the user can only select a departure date
  // in the allowed departure date range
  const minimumDays = !value.arrivalDate
    ? 1
    : Math.max(1, moment(departureDateFrom).diff(moment(value.arrivalDate), 'days') + 1);

  return (
    <>
      <ul styleName="radio-group">
        {choices
          .filter(c => c.isEnabled || !c.isNoAccommodation) // show disabled unless no accommodation
          .map(c => (
            <li key={c.id}>
              <input
                type="radio"
                name={htmlName}
                id={`${htmlName}-${c.id}`}
                value={c.id}
                disabled={!c.isEnabled || disabled}
                checked={c.id === value.choice}
                onChange={makeHandleChange(c)}
              />{' '}
              <label htmlFor={`${htmlName}-${c.id}`}>{c.caption}</label>
            </li>
          ))}
      </ul>
      <DatePeriodField
        onChange={handleDateChange}
        onFocus={() => undefined}
        onBlur={() => undefined}
        disabled={value.choice === null || value.isNoAccommodation}
        disabledDate={isDateDisabled}
        initialVisibleMonth={() => arrivalDateFrom}
        onFieldFocusChange={setFocusedDateField}
        minimumDays={minimumDays}
        value={{startDate: value.arrivalDate, endDate: value.departureDate}}
        extraPickerProps={{
          noBorder: true,
          block: false,
          small: true,
          startDatePlaceholderText: Translate.string('Arrival'),
          endDatePlaceholderText: Translate.string('Departure'),
        }}
      />
    </>
  );
}

AccommodationInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  arrival: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  departure: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

AccommodationInput.defaultProps = {
  disabled: false,
};

export const accommodationSettingsInitialData = staticData => ({
  choices: [
    {
      id: `new:no-accommodation`,
      caption: 'No accommodation',
      isEnabled: true,
      isBillable: false,
      isNoAccommodation: true,
      price: 0,
      placesLimit: 0,
    },
  ],
  arrival: {
    startDate: serializeDate(
      toMoment(staticData.eventStartDate, moment.HTML5_FMT.DATE).subtract(2, 'days')
    ),
    endDate: serializeDate(toMoment(staticData.eventEndDate, moment.HTML5_FMT.DATE)),
  },
  departure: {
    startDate: serializeDate(
      toMoment(staticData.eventStartDate, moment.HTML5_FMT.DATE).add(1, 'days')
    ),
    endDate: serializeDate(toMoment(staticData.eventEndDate, moment.HTML5_FMT.DATE).add(3, 'days')),
  },
});

export function accommodationSettingsFormValidator({arrival, departure}) {
  const arrivalDateFrom = toMoment(arrival.startDate, moment.HTML5_FMT.DATE);
  const arrivalDateTo = toMoment(arrival.endDate, moment.HTML5_FMT.DATE);
  const departureDateFrom = toMoment(departure.startDate, moment.HTML5_FMT.DATE);
  const departureDateTo = toMoment(departure.endDate, moment.HTML5_FMT.DATE);

  const errors = {};
  let dataMissing = false;
  if (!arrivalDateFrom || !arrivalDateTo) {
    errors.arrival = Translate.string('This field is required.');
    dataMissing = true;
  }
  if (!departureDateFrom || !departureDateTo) {
    errors.departure = Translate.string('This field is required.');
    dataMissing = true;
  }
  if (dataMissing) {
    return errors;
  }

  if (departureDateFrom.isBefore(arrivalDateFrom)) {
    errors.departure = Translate.string(
      'The departure period cannot begin before the arrival period.'
    );
  }
  if (arrivalDateTo.isAfter(departureDateTo)) {
    errors.arrival = Translate.string('The arrival period cannot end after the departure period.');
  }
  return errors;
}

export function AccommodationSettings() {
  return (
    <>
      <FinalDatePeriod
        name="arrival"
        label={Translate.string('Arrival')}
        disabledDate={() => false}
        extraPickerProps={{noBorder: true}}
        required
      />
      <FinalDatePeriod
        name="departure"
        label={Translate.string('Departure')}
        disabledDate={() => false}
        extraPickerProps={{noBorder: true}}
        required
      />
      <FinalField
        name="choices"
        label={Translate.string('Choices')}
        component={Choices}
        isEqual={_.isEqual}
        forAccommodation
        required
        validate={val => {
          if (!val.some(c => c.isEnabled)) {
            return Translate.string('You need to have at least one enabled option.');
          }
        }}
      />
    </>
  );
}
