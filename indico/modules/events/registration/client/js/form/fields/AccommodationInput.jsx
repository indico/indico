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
import {useSelector} from 'react-redux';
import {Label} from 'semantic-ui-react';

import {DateRangePicker, RadioButton} from 'indico/react/components';
import {FinalDateRangePicker} from 'indico/react/components/DateRangePicker';
import {FinalField} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';

import {getPriceFormatter} from '../../form/selectors';
import {getFieldValue, getManagement, getPaid} from '../../form_submission/selectors';

import ChoiceLabel from './ChoiceLabel';
import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';
import './table.module.scss';

function AccommodationInputComponent({
  id,
  existingValue,
  value,
  onChange,
  disabled,
  isPurged,
  choices,
  arrival,
  departure,
  placesUsed,
}) {
  const paid = useSelector(getPaid);
  const management = useSelector(getManagement);
  const formatPrice = useSelector(getPriceFormatter);
  const selectedChoice = choices.find(c => c.id === value.choice);

  const makeHandleChange = choice => () => {
    const newValue = {...value, choice: choice.id, isNoAccommodation: choice.isNoAccommodation};
    if (choice.isNoAccommodation) {
      delete newValue.arrivalDate;
      delete newValue.departureDate;
    }
    onChange(newValue);
  };

  const handleDateChange = ({startDate = null, endDate = null}) => {
    onChange({...value, arrivalDate: startDate, departureDate: endDate});
  };

  const nights =
    value.arrivalDate && value.departureDate
      ? moment(value.departureDate).diff(moment(value.arrivalDate), 'days')
      : 0;

  const isPaidChoice = choice => choice.price > 0 && paid;
  const isPaidChoiceLocked = choice => !management && isPaidChoice(choice);

  return (
    <div styleName="accommodation-field">
      <table styleName="choice-table" role="presentation" id={id}>
        <tbody>
          {choices
            .filter(c => c.isEnabled || !c.isNoAccommodation)
            .map((c, index) => {
              return (
                <tr key={c.id} styleName="row">
                  <td>
                    <RadioButton
                      id={id ? `${id}-${index}` : ''}
                      name={id}
                      key={c.id}
                      value={c.id}
                      checked={!isPurged && c.id === value.choice}
                      disabled={
                        !c.isEnabled ||
                        disabled ||
                        isPaidChoiceLocked(c) ||
                        (c.placesLimit > 0 &&
                          (placesUsed[c.id] || 0) >= c.placesLimit &&
                          c.id !== existingValue.choice)
                      }
                      label={
                        <ChoiceLabel choice={c} management={management} paid={isPaidChoice(c)} />
                      }
                      onChange={makeHandleChange(c)}
                    />
                  </td>
                  <td>
                    {c.isEnabled && !!c.price && (
                      <Label pointing="left">
                        <Translate>
                          <Param name="price" value={formatPrice(c.price)} /> per night
                        </Translate>
                      </Label>
                    )}
                  </td>
                  <td>
                    {c.placesLimit === 0 ? null : (
                      <PlacesLeft
                        placesLimit={c.placesLimit}
                        placesUsed={placesUsed[c.id] || 0}
                        isEnabled={!disabled && c.isEnabled && !isPaidChoiceLocked(c)}
                      />
                    )}
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
      {value.choice !== null && !value.isNoAccommodation && (
        <div styleName="date-picker">
          <DateRangePicker
            label={Translate.string('Pick the arrival and departure dates')}
            onChange={handleDateChange}
            value={{
              startDate: value.arrivalDate || '',
              endDate: value.departureDate || '',
            }}
            rangeStartLabel={Translate.string('Arrival')}
            rangeEndLabel={Translate.string('Departure')}
            rangeStartMin={arrival.startDate}
            rangeStartMax={arrival.endDate}
            rangeEndMin={departure.startDate}
            rangeEndMax={departure.endDate}
          />
          {!!selectedChoice.price && (
            <Label pointing="left" styleName="price-tag">
              <Translate>
                Total:{' '}
                <Param name="price" value={formatPrice((nights || 0) * selectedChoice.price)} />
              </Translate>
            </Label>
          )}
        </div>
      )}
    </div>
  );
}

AccommodationInputComponent.propTypes = {
  id: PropTypes.string.isRequired,
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  isPurged: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  arrival: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  departure: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.shape({choice: PropTypes.string}).isRequired,
};

export default function AccommodationInput({
  fieldId,
  htmlId,
  htmlName,
  disabled,
  isRequired,
  isPurged,
  choices,
  arrival,
  departure,
  placesUsed,
}) {
  const existingValue = useSelector(state => getFieldValue(state, fieldId)) || {choice: null};
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      existingValue={existingValue}
      component={AccommodationInputComponent}
      required={isRequired}
      disabled={disabled}
      isPurged={isPurged}
      choices={choices}
      arrival={arrival}
      departure={departure}
      placesUsed={placesUsed}
      validate={value => {
        if (value.choice === null) {
          return isRequired ? Translate.string('You must select an option') : undefined;
        } else if (!value.isNoAccommodation && (!value.arrivalDate || !value.departureDate)) {
          return Translate.string('You must select the arrival and departure date');
        }
      }}
      isEqual={_.isEqual}
    />
  );
}

AccommodationInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  isPurged: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  arrival: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  departure: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string.isRequired,
  }).isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
};

AccommodationInput.defaultProps = {
  disabled: false,
  isRequired: false,
};

export const accommodationSettingsInitialData = staticData => ({
  choices: [
    {
      id: `new:no-accommodation`,
      caption: 'No accommodation',
      isEnabled: true,
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
  if (!arrivalDateFrom || !arrivalDateTo || !departureDateFrom || !departureDateTo) {
    // already covered by field-level validation
    return;
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
      <FinalDateRangePicker name="arrival" label={Translate.string('Arrival')} required />
      <FinalDateRangePicker
        name="departure"
        label={Translate.string('Departure')}
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

export function accommodationShowIfOptions(field) {
  return field.choices.map(({caption, id}) => ({value: id, text: caption}));
}

export function accommodationGetDataForCondition(value) {
  return [value.choice];
}
