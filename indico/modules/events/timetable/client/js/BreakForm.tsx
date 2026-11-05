// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import {Field} from 'react-final-form';

import {FinalLocationField, FinalSessionColorPicker} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDuration} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {LocationParentObj} from './types';

interface BreakFormFieldsProps {
  locationParent?: LocationParentObj;
  initialValues: Record<string, any>;
  extraOptions?: Record<string, any>;
  hasParent?: boolean;
  [key: string]: any; // Allow additional props
}

export function BreakFormFields({
  locationParent = {
    inheriting: false,
    venue: '',
    room: '',
    venue_name: '',
    room_name: '',
    address: '',
  },
  initialValues = {},
  extraOptions = {},
  hasParent = false,
}: BreakFormFieldsProps) {
  const {minStartDt, maxEndDt} = extraOptions;

  return (
    <>
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      {initialValues.start_dt ? (
        <>
          <Field name="duration" subscription={{value: true}}>
            {({input: {value: duration}}) => (
              <FinalDateTimePicker
                name="start_dt"
                label={Translate.string('Start date')}
                minStartDt={minStartDt}
                maxEndDt={maxEndDt ? maxEndDt.clone().subtract(duration, 'seconds') : null}
                required
              />
            )}
          </Field>
          <Field name="start_dt" subscription={{value: true}}>
            {({input: {value: startDt}}) => (
              <FinalDuration
                name="duration"
                label={Translate.string('Duration')}
                max={maxEndDt ? moment(maxEndDt).diff(startDt, 'seconds') : null}
              />
            )}
          </Field>
        </>
      ) : (
        <FinalDuration name="duration" label={Translate.string('Duration')} />
      )}
      <FinalLocationField
        name="location_data"
        label={Translate.string('Location')}
        locationParent={locationParent}
      />
      {!hasParent && <FinalSessionColorPicker name="colors" label={Translate.string('Color')} />}
    </>
  );
}
