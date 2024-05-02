// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useMemo} from 'react';
import {useForm} from 'react-final-form';
import {useSelector} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import {getFlatFieldList} from './selectors';
import './FormErrorList.module.scss';

export default function FormErrorList() {
  const formFieldList = useSelector(getFlatFieldList);
  const fieldLabelLookup = useMemo(() => {
    const lookup = new Map();
    for (const formField of formFieldList) {
      lookup.set(formField.htmlName, {
        label: formField.title,
        id: `input-${formField.id}`,
      });
    }
    lookup.set('captcha', {
      label: Translate.string('Captcha'),
      id: 'input-captcha',
    });
    return lookup;
  }, [formFieldList]);

  const {errors} = useForm().getState();
  const fieldsWithErrors = [];

  for (const fieldName in errors) {
    const field = fieldLabelLookup.get(fieldName);

    // Check for misbehaving fields. This is for developers.
    if (!field) {
      console.warn(
        `FormErrorList: Field ${fieldName} is not registered with the final form and will not be shown in the erorr list`
      );
      continue;
    }

    fieldsWithErrors.push({label: field.label, id: field.id, message: errors[fieldName]});
  }

  function focusField(evt) {
    evt.preventDefault();
    const id = evt.target.href.split('#')[1];
    const element = document.getElementById(id);

    if (!element) {
      // This is a programmer error. All fields *must* have an id.
      console.warn(
        'FormError: #${id} does not match a form field. Please make sure all form fields have an appropriate id.'
      );
      return;
    }

    // Some widget don't put id on the form control itself but the outer wrapper.
    // We will first try the element, and if it's not a form control, we'll look
    // for one in the subtree.
    if (element.matches('input,select,textarea,button')) {
      element.focus();
    } else {
      // We exclude the file field because it's likely controlled by something else
      element.querySelector('input:not([type=file]),select,textarea,button')?.focus();
    }
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
