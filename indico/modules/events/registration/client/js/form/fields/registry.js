// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';

import InputBoolean, {BooleanSettings} from './InputBoolean';
import InputCheckbox from './InputCheckbox';
import InputCountry from './InputCountry';
import InputEmail from './InputEmail';
import InputLabel from './InputLabel';
import InputNumber, {NumberSettings, numberSettingsFormValidator} from './InputNumber';
import InputPhone from './InputPhone';
import InputSingleChoice, {
  SingleChoiceSettings,
  singleChoiceSettingsFormDecorator,
  singleChoiceSettingsInitialData,
} from './InputSingleChoice';
import InputText, {TextSettings} from './InputText';
import InputTextArea, {TextAreaSettings} from './InputTextArea';

/*
Available keys:
- title: required; used to show the field type when adding a new field
- inputComponent: required; the component used to render the field
- settingsComponent: optional; used if the field has custom settings
- settingsModalSize: optional; used if the field has settings which benefit
  from a larger modal size than "tiny"
- settingsFormDecorator: optional; a final-form decorator to apply to the
  settings form
- settingsFormValidator: optional, a function for final-form's form-level validation
- settingsFormInitialData: optional; initial data to use when creating a new
  field in case some of the settings need to be initialized
- noLabel: optional; render the field without a label on the left
- noRequired: optional; hide the option to make the field required
*/

export const fieldRegistry = {
  label: {
    title: Translate.string('Static label'),
    inputComponent: InputLabel,
    noRequired: true,
    noLabel: true,
  },
  text: {
    title: Translate.string('Text'),
    inputComponent: InputText,
    settingsComponent: TextSettings,
  },
  number: {
    title: Translate.string('Number'),
    inputComponent: InputNumber,
    settingsComponent: NumberSettings,
    settingsFormValidator: numberSettingsFormValidator,
  },
  textarea: {
    title: Translate.string('Text area'),
    inputComponent: InputTextArea,
    settingsComponent: TextAreaSettings,
  },
  checkbox: {
    title: Translate.string('Checkbox'),
    inputComponent: InputCheckbox,
    noLabel: true,
  },
  bool: {
    title: Translate.string('Yes/No'),
    inputComponent: InputBoolean,
    settingsComponent: BooleanSettings,
  },
  phone: {
    title: Translate.string('Phone'),
    inputComponent: InputPhone,
  },
  country: {
    title: Translate.string('Country'),
    inputComponent: InputCountry,
  },
  email: {
    title: Translate.string('Email'),
    inputComponent: InputEmail,
  },
  single_choice: {
    title: Translate.string('Single Choice'),
    inputComponent: InputSingleChoice,
    settingsComponent: SingleChoiceSettings,
    settingsModalSize: 'small',
    settingsFormDecorator: singleChoiceSettingsFormDecorator,
    settingsFormInitialData: singleChoiceSettingsInitialData,
  },
  // TODO add other input types
};
