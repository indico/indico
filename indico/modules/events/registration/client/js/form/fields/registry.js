// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';

import AccommodationInput, {
  AccommodationSettings,
  accommodationSettingsInitialData,
  accommodationSettingsFormValidator,
} from './AccommodationInput';
import BooleanInput, {BooleanSettings} from './BooleanInput';
import CheckboxInput, {CheckboxSettings} from './CheckboxInput';
import CountryInput from './CountryInput';
import DateInput, {
  DateSettings,
  dateSettingsFormDecorator,
  dateSettingsInitialData,
} from './DateInput';
import EmailInput from './EmailInput';
import FileInput from './FileInput';
import LabelInput from './LabelInput';
import MultiChoiceInput, {
  MultiChoiceSettings,
  multiChoiceSettingsInitialData,
} from './MultiChoiceInput';
import NumberInput, {NumberSettings, numberSettingsFormValidator} from './NumberInput';
import PhoneInput from './PhoneInput';
import SingleChoiceInput, {
  SingleChoiceSettings,
  singleChoiceSettingsFormDecorator,
  singleChoiceSettingsInitialData,
} from './SingleChoiceInput';
import TextAreaInput, {TextAreaSettings} from './TextAreaInput';
import TextInput, {TextSettings} from './TextInput';

/*
Available keys:
- title: required; used to show the field type when adding a new field
- icon: required; used in the add field dropdown (this uses an indico icon, not a SUI icon)
- inputComponent: required; the component used to render the field
- settingsComponent: optional; used if the field has custom settings
- settingsModalSize: optional; used if the field has settings which benefit
  from a larger modal size than "tiny"
- settingsFormDecorator: optional; a final-form decorator to apply to the
  settings form
- settingsFormValidator: optional, a function for final-form's form-level validation
- settingsFormInitialData: optional; initial data to use when creating a new
  field in case some of the settings need to be initialized. if it's a callable, the
  staticData from the state will be passed to it
- noLabel: optional; render the field without a label on the left
- noRequired: optional; hide the option to make the field required
- alwaysRequired: optional; always display the field as required
- hasPrice: optional; show price field if the whole field can have a price attached
*/

export const fieldRegistry = {
  label: {
    title: Translate.string('Static label'),
    inputComponent: LabelInput,
    noRequired: true,
    noLabel: true,
    icon: 'tag',
    customFormItem: true,
  },
  text: {
    title: Translate.string('Text'),
    inputComponent: TextInput,
    settingsComponent: TextSettings,
    icon: 'textfield',
  },
  number: {
    title: Translate.string('Number'),
    inputComponent: NumberInput,
    settingsComponent: NumberSettings,
    settingsFormValidator: numberSettingsFormValidator,
    hasPrice: true,
    icon: 'seven-segment9',
  },
  textarea: {
    title: Translate.string('Text area'),
    inputComponent: TextAreaInput,
    settingsComponent: TextAreaSettings,
    icon: 'textarea',
  },
  checkbox: {
    title: Translate.string('Checkbox'),
    inputComponent: CheckboxInput,
    settingsComponent: CheckboxSettings,
    noLabel: true,
    hasPrice: true,
    icon: 'checkbox-checked',
    customFormItem: true,
  },
  date: {
    title: Translate.string('Date'),
    inputComponent: DateInput,
    settingsComponent: DateSettings,
    settingsFormDecorator: dateSettingsFormDecorator,
    settingsFormInitialData: dateSettingsInitialData,
    icon: 'calendar',
  },
  bool: {
    title: Translate.string('Yes/No'),
    inputComponent: BooleanInput,
    settingsComponent: BooleanSettings,
    hasPrice: true,
    icon: 'switchon',
    customFormItem: true,
  },
  phone: {
    title: Translate.string('Phone'),
    inputComponent: PhoneInput,
    icon: 'phone',
  },
  country: {
    title: Translate.string('Country'),
    inputComponent: CountryInput,
    icon: 'earth',
  },
  file: {
    title: Translate.string('File'),
    inputComponent: FileInput,
    icon: 'upload',
  },
  email: {
    title: Translate.string('Email'),
    inputComponent: EmailInput,
    icon: 'mail',
  },
  single_choice: {
    title: Translate.string('Single Choice'),
    inputComponent: SingleChoiceInput,
    settingsComponent: SingleChoiceSettings,
    settingsModalSize: 'small',
    settingsFormDecorator: singleChoiceSettingsFormDecorator,
    settingsFormInitialData: singleChoiceSettingsInitialData,
    icon: 'dropmenu',
  },
  multi_choice: {
    title: Translate.string('Multiple Choice'),
    inputComponent: MultiChoiceInput,
    settingsComponent: MultiChoiceSettings,
    settingsModalSize: 'small',
    settingsFormInitialData: multiChoiceSettingsInitialData,
    icon: 'list',
  },
  accommodation: {
    title: Translate.string('Accommodation'),
    inputComponent: AccommodationInput,
    settingsComponent: AccommodationSettings,
    settingsModalSize: 'small',
    settingsFormInitialData: accommodationSettingsInitialData,
    settingsFormValidator: accommodationSettingsFormValidator,
    noRequired: true,
    alwaysRequired: true,
    icon: 'home',
  },
};
