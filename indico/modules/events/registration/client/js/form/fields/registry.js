// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import InputBoolean, {BooleanSettings} from './InputBoolean';
import InputCountry from './InputCountry';
import InputLabel from './InputLabel';
import InputNumber, {NumberSettings} from './InputNumber';
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
- settingsFormInitialData: optional; initial data to use when creating a new
  field in case some of the settings need to be initialized
- noLabel: optional; render the field without a label on the left
- noRequired: optional; hide the option to make the field required
*/

export const fieldRegistry = {
  label: {
    title: 'Static label',
    inputComponent: InputLabel,
    noRequired: true,
    noLabel: true,
  },
  text: {
    title: 'Text field',
    inputComponent: InputText,
    settingsComponent: TextSettings,
  },
  number: {
    title: 'Number',
    inputComponent: InputNumber,
    settingsComponent: NumberSettings,
  },
  textarea: {
    title: 'Text area',
    inputComponent: InputTextArea,
    settingsComponent: TextAreaSettings,
  },
  bool: {
    title: 'Boolean',
    inputComponent: InputBoolean,
    settingsComponent: BooleanSettings,
  },
  phone: {
    title: 'Phone',
    inputComponent: InputPhone,
  },
  country: {
    title: 'Country',
    inputComponent: InputCountry,
  },
  single_choice: {
    title: 'Single Choice',
    inputComponent: InputSingleChoice,
    settingsComponent: SingleChoiceSettings,
    settingsModalSize: 'small',
    settingsFormDecorator: singleChoiceSettingsFormDecorator,
    settingsFormInitialData: singleChoiceSettingsInitialData,
  },
  // TODO add other input types
};
