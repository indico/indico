// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useFormState} from 'react-final-form';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import {getFieldLabelLookup} from './selectors';
import './FormErrorList.module.scss';

const FOCUSABLE_INPUTS = 'input:not([type=hidden]):not([type=file]),button,select,textarea';
const SPECIAL_FIELDS = {
  agreed_to_privacy_policy: {
    label: Translate.string('Privacy policy'),
    id: 'finalfield-agreed_to_privacy_policy',
  },
  consent_to_publish: {
    label: Translate.string('Participant list'),
    id: 'input-consent-to-publish',
  },
};

export default function FormErrorList() {
  const fieldLabelLookup = useSelector(getFieldLabelLookup);
  const {errors} = useFormState({errors: true});

  const fieldsWithErrors = [];
  for (const fieldName in errors) {
    const field = fieldLabelLookup.get(fieldName) || SPECIAL_FIELDS[fieldName];

    // Check for misbehaving fields. This is for developers.
    if (!field) {
      console.warn(
        `FormErrorList: Field ${fieldName} is not registered with the final form and will not be shown in the error list`
      );
      continue;
    }

    fieldsWithErrors.push({...field, message: errors[fieldName]});
  }

  function focusField(evt) {
    evt.preventDefault();
    const id = evt.target.href.split('#')[1];
    let element = document.getElementById(id);

    // If the element is not the actual input (e.g., it's a fieldset)
    // drill down to locate the element
    if (element && !element.matches(FOCUSABLE_INPUTS) && !element.tagName.startsWith('IND-')) {
      element = element.querySelector(FOCUSABLE_INPUTS);
    }

    if (!element) {
      // This is a programmer error. All fields *must* have an id.
      console.warn(
        `FormErrorList: #${id} does not match a form field. Please make sure all form fields or their containing fieldset have an appropriate id.`
      );
      return;
    }

    element.focus();
  }

  if (!fieldsWithErrors.length) {
    return null;
  }

  return (
    <div styleName="form-error-list">
      <Translate as="h4">You need to review some of the fields</Translate>

      <ul aria-label={Translate.string('Fields with errors')}>
        {fieldsWithErrors.map(field => (
          <li key={field.id}>
            <a
              href={`#${field.id}`}
              aria-label={Translate.string('Visit incomplete field {field}: {error}', {
                field: field.label,
                error: field.message,
              })}
              onClick={focusField}
            >
              {field.label}: {field.message}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
