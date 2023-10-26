// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React from 'react';
import {Field} from 'react-final-form';
import {Form, Input} from 'semantic-ui-react';

import {SingleDatePicker} from 'indico/react/components';
import {FinalDropdown, FinalField, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';

import '../../../styles/regform.module.scss';

function DateInputComponent({value, onChange, disabled, required, dateFormat, timeFormat}) {
  const dateValue = value.split('T')[0];
  const timeValue = value.includes('T') ? value.split('T')[1] : '';

  const handleDateChange = newDate => {
    const dateString = newDate ? newDate.toISOString().split('T')[0] : '';
    const timeString = timeFormat ? timeValue : '00:00:00';
    onChange(`${dateString}T${timeString}`);
  };
  const handleTimeChange = newTime =>
    onChange(newTime ? `${dateValue}T${newTime.format('HH:mm:00')}` : dateValue);

  return (
    <Form.Group styleName="date-field">
      <Form.Field>
        <SingleDatePicker
          name="date"
          disabled={disabled}
          required={required}
          date={toMoment(dateValue, 'YYYY-MM-DD', true)}
          onDateChange={handleDateChange}
          placeholder={dateFormat}
          displayFormat={dateFormat}
          isOutsideRange={() => false}
          verticalSpacing={10}
          enableOutsideDays
        />
      </Form.Field>
      {timeFormat && (
        <Form.Field>
          <TimePicker
            name="time"
            disabled={disabled}
            required={required}
            showSecond={false}
            value={toMoment(timeValue, 'HH:mm:ss', true)}
            focusOnOpen
            onChange={handleTimeChange}
            use12Hours={timeFormat === '12h'}
            allowEmpty={false}
            placeholder={timeFormat === '12h' ? '--:-- am/pm' : '--:--'}
            getPopupContainer={node => node}
          />
        </Form.Field>
      )}
    </Form.Group>
  );
}

DateInputComponent.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  required: PropTypes.bool.isRequired,
  dateFormat: PropTypes.oneOf([
    'DD/MM/YYYY',
    'DD.MM.YYYY',
    'MM/DD/YYYY',
    'MM.DD.YYYY',
    'YYYY/MM/DD',
    'YYYY.MM.DD',
    'MM/YYYY',
    'MM.YYYY',
    'YYYY',
  ]).isRequired,
  timeFormat: PropTypes.oneOf(['12h', '24h']),
};

DateInputComponent.defaultProps = {
  timeFormat: null,
};

export default function DateInput({htmlName, disabled, isRequired, dateFormat, timeFormat}) {
  const friendlyDateFormat = dateFormat.replace(
    /%([HMdmY])/g,
    (match, c) => ({H: 'HH', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c])
  );
  const validateDateTime = dateTime => {
    if (dateTime && !dateTime.match(/\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:00(.*)/)) {
      return Translate.string('The provided date is invalid.');
    }
  };

  if (dateFormat.includes('%d')) {
    return (
      <FinalField
        name={htmlName}
        component={DateInputComponent}
        required={isRequired}
        disabled={disabled}
        dateFormat={friendlyDateFormat}
        timeFormat={timeFormat}
        validate={validateDateTime}
      />
    );
  } else {
    const parseDate = date => {
      if (!date) {
        return date;
      }
      const regexps = {
        '%m/%Y': /^(?<month>\d{2})\/(?<year>\d{4})$/,
        '%m.%Y': /^(?<month>\d{2})\.(?<year>\d{4})$/,
        '%Y': /^(?<year>\d{4})$/,
      };
      const match = regexps[dateFormat].exec(date);
      const rv = match ? `${match.groups.year}-${match.groups.month ?? '01'}-01T00:00:00` : date;
      try {
        toMoment(rv, 'YYYY-MM-DDTHH:mm:ss', true);
        return rv;
      } catch (e) {
        return date;
      }
    };
    const formatDate = date => {
      if (!date || !date.includes('T')) {
        return date;
      }
      try {
        return toMoment(date, 'YYYY-MM-DDTHH:mm:ss', true).format(friendlyDateFormat);
      } catch (e) {
        return date;
      }
    };
    return (
      <FinalField
        type="text"
        name={htmlName}
        component={Input}
        required={isRequired}
        disabled={disabled}
        placeholder={friendlyDateFormat}
        parse={parseDate}
        format={formatDate}
        validate={validateDateTime}
      />
    );
  }
}

DateInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  dateFormat: PropTypes.oneOf([
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ]).isRequired,
  timeFormat: PropTypes.oneOf(['12h', '24h']),
};

DateInput.defaultProps = {
  disabled: false,
  isRequired: false,
  timeFormat: null,
};

export const dateSettingsFormDecorator = createDecorator({
  field: 'dateFormat',
  updates: dateFormat => {
    // clear the time format when it doesn't make sense for the selected date format
    if (!dateFormat.includes('%d')) {
      return {timeFormat: null};
    }
    return {};
  },
});

export const dateSettingsInitialData = {
  dateFormat: '%d/%m/%Y',
  timeFormat: null,
};

export function DateSettings() {
  const dateOptions = [
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ].map(opt => ({
    key: opt,
    value: opt,
    text: opt.replace(
      /%([HMdmY])/g,
      (match, c) => ({H: 'hh', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c])
    ),
  }));
  const timeOptions = [
    {key: '12h', value: '12h', text: Translate.string('12 hours')},
    {key: '24h', value: '24h', text: Translate.string('24 hours')},
  ];
  return (
    <Form.Group widths="equal">
      <FinalDropdown
        name="dateFormat"
        label={Translate.string('Date format')}
        options={dateOptions}
        required
        selection
        fluid
      />
      <Field name="dateFormat" subscription={{value: true}}>
        {({input: {value: dateFormat}}) => (
          <FinalDropdown
            name="timeFormat"
            label={Translate.string('Time format')}
            options={timeOptions}
            placeholder={Translate.string('None')}
            disabled={!dateFormat.includes('%d')}
            parse={p.nullIfEmpty}
            selection
            fluid
          />
        )}
      </Field>
    </Form.Group>
  );
}
