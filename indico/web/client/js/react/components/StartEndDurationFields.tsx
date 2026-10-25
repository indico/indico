// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment, {Moment} from 'moment';
import React, {useEffect, useState} from 'react';
import {Field, useForm} from 'react-final-form';
import {Form, Input} from 'semantic-ui-react';

import {FinalDateTimePicker, FinalField} from 'indico/react/forms/fields';
import validators from 'indico/react/forms/validators';
import {Translate} from 'indico/react/i18n';

const DT_FORMAT = 'YYYY-MM-DDTHH:mm:ss';

export const getEndDt = (startDt: string, duration: number) =>
  moment(startDt).add(duration, 'seconds').format(DT_FORMAT);

export const withoutEndDt = (values: Record<string, any>) => _.omit(values, 'end_dt');

const isValidDatetime = validators.datetime();

const validateEndDt = (endDt: string, values: Record<string, any>) => {
  const invalid = isValidDatetime(endDt);
  if (invalid) {
    return invalid;
  } else if (!moment(endDt).isSame(values.start_dt, 'day')) {
    return Translate.string('An entry must start and end on the same day.');
  } else if (!moment(endDt).isAfter(values.start_dt)) {
    return Translate.string('An entry must end after it starts.');
  }
};

const formatDuration = (seconds: number) => {
  const minutes = Math.floor(Math.max(0, seconds || 0) / 60);
  return `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}`;
};

const parseDuration = (text: string) => {
  const match = /^\s*(\d*)\s*(?::\s*(\d{1,2})\s*)?$/.exec(text);
  if (!match || (!match[1] && !match[2])) {
    return null;
  }
  const minutes = parseInt(match[2] || '0', 10);
  if (minutes > 59) {
    return null;
  }
  return parseInt(match[1] || '0', 10) * 3600 + minutes * 60;
};

interface HoursDurationComponentProps {
  value: number;
  onChange: (value: number) => void;
  onBlur: () => void;
  onFocus: () => void;
  disabled?: boolean;
  required?: boolean;
}

function HoursDurationComponent({
  value,
  onChange,
  onBlur,
  onFocus,
  disabled,
  required,
}: HoursDurationComponentProps) {
  const [text, setText] = useState(() => formatDuration(value));

  useEffect(() => setText(formatDuration(value)), [value]);

  const commit = () => {
    const seconds = parseDuration(text);
    setText(formatDuration(seconds === null ? value : seconds));
    if (seconds !== null && seconds !== value) {
      onChange(seconds);
    }
    onBlur();
  };

  return (
    <Input
      value={text}
      disabled={disabled}
      required={required}
      placeholder="h:mm"
      onFocus={onFocus}
      onChange={(evt, {value: v}) => setText(v)}
      onBlur={commit}
      onKeyDown={(evt: React.KeyboardEvent) => {
        if (evt.key === 'Enter') {
          evt.preventDefault();
          commit();
        }
      }}
    />
  );
}

export function FinalHoursDuration({
  name,
  label,
  defaultValue = 20 * 60,
  ...rest
}: {
  name: string;
  label?: string;
  defaultValue?: number;
  required?: boolean;
  onChange?: (newValue: number, oldValue: number) => void;
  fieldProps?: object;
}) {
  return (
    <FinalField
      name={name}
      component={HoursDurationComponent}
      label={label}
      defaultValue={defaultValue}
      {...rest}
    />
  );
}

interface StartEndDurationFieldsProps {
  minStartDt?: Moment;
  maxEndDt?: Moment;
}

export default function StartEndDurationFields({
  minStartDt,
  maxEndDt,
}: StartEndDurationFieldsProps) {
  const form = useForm();
  const getValue = (name: string) => form.getState().values[name];
  const [initialEndDt] = useState(() => {
    const {start_dt: startDt, duration} = form.getState().initialValues;
    return startDt ? getEndDt(startDt, duration || 0) : undefined;
  });

  const handleStartChange = (startDt: string) => {
    const endDt = getValue('end_dt');
    const duration = moment(endDt).diff(startDt, 'seconds');
    if (duration > 0 && moment(endDt).isSame(startDt, 'day')) {
      form.change('duration', duration);
    } else {
      form.change('end_dt', getEndDt(startDt, getValue('duration')));
    }
  };

  const handleEndChange = (endDt: string) =>
    form.change('duration', moment(endDt).diff(getValue('start_dt'), 'seconds'));

  const handleDurationChange = (duration: number) =>
    form.change('end_dt', getEndDt(getValue('start_dt'), duration));

  // the end cannot leave the start's day, so the end picker's calendar is locked to it
  const latestEnd = (startDt: string) => {
    const dayEnd = moment(startDt).endOf('day');
    return maxEndDt?.isBefore(dayEnd) ? maxEndDt : dayEnd;
  };

  return (
    <>
      <Form.Group>
        <FinalDateTimePicker
          name="start_dt"
          label={Translate.string('Start date')}
          minStartDt={minStartDt}
          maxEndDt={maxEndDt}
          onChange={handleStartChange}
          fieldProps={{style: {flex: '0 0 auto'}}}
          required
        />
        <FinalHoursDuration
          name="duration"
          label={Translate.string('Duration')}
          onChange={handleDurationChange}
          fieldProps={{style: {flex: '0 0 auto', width: '10em'}}}
          required
        />
      </Form.Group>
      <Field name="start_dt" subscription={{value: true}}>
        {({input: {value: startDt}}) => (
          <FinalDateTimePicker
            name="end_dt"
            label={Translate.string('End date')}
            initialValue={initialEndDt}
            minStartDt={moment(startDt)}
            maxEndDt={latestEnd(startDt)}
            onChange={handleEndChange}
            validate={validateEndDt}
            hideValidationError="never"
            required
          />
        )}
      </Field>
    </>
  );
}
