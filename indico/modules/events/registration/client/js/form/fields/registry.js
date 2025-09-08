// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Translate} from 'indico/react/i18n';
import {getPluginObjects} from 'indico/utils/plugins';

import AccommodationInput, {
  AccommodationSettings,
  accommodationSettingsFormValidator,
  accommodationSettingsInitialData,
  accommodationShowIfOptions,
  accommodationGetDataForCondition,
} from './AccommodationInput';
import AccompanyingPersonsInput, {
  AccompanyingPersonsSettings,
  accompanyingPersonsSettingsInitialData,
} from './AccompanyingPersonsInput';
import BooleanInput, {
  BooleanSettings,
  booleanShowIfOptions,
  booleanGetDataForCondition,
} from './BooleanInput';
import CheckboxInput, {
  CheckboxSettings,
  checkboxShowIfOptions,
  checkboxGetDataForCondition,
} from './CheckboxInput';
import {choiceFieldsSettingsFormDecorator} from './ChoicesSetup';
import CountryInput, {CountrySettings} from './CountryInput';
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
  multiChoiceShowIfOptions,
  multiChoiceGetDataForCondition,
} from './MultiChoiceInput';
import NumberInput, {NumberSettings, numberSettingsFormValidator} from './NumberInput';
import PhoneInput from './PhoneInput';
import PictureInput, {PictureSettings} from './PictureInput';
import SingleChoiceInput, {
  SingleChoiceSettings,
  singleChoiceSettingsFormDecorator,
  singleChoiceSettingsInitialData,
  singleChoiceShowIfOptions,
  singleChoiceGetDataForCondition,
} from './SingleChoiceInput';
import TextAreaInput, {TextAreaSettings} from './TextAreaInput';
import TextInput, {TextSettings, textSettingsFormValidator} from './TextInput';
import TimetableSessionsInput, {
  sessionsSettingsFormValidator,
  TimetableSessionsSettings,
  timetableSessionsSettingsInitialData,
} from './TimetableSessions';

/*
Available keys:
- title: required; used to show the field type when adding a new field
- icon: required; used in the add field dropdown (this uses an indico icon, not a SUI icon)
- inputComponent: required; the component used to render the field
- settingsComponent: optional; used if the field has custom settings
- settingsModalSize: optional; used if the field has settings which benefit
  from a larger modal size than "tiny"
- settingsFormDecorators: optional; the final-form decorators to apply to the
  settings form
- settingsFormValidator: optional, a function for final-form's form-level validation
- settingsFormInitialData: optional; initial data to use when creating a new
  field in case some of the settings need to be initialized. if it's a callable, the
  staticData from the state will be passed to it
- noLabel: optional; render the field without a label on the left
- noRequired: optional; hide the option to make the field required
- alwaysRequired: optional; always display the field as required
- hasPrice: optional; show price field if the whole field can have a price attached
- noRetentionPeriod: optional; hide the retention period setting
- renderAsFieldset: optional; whether the field should be rendered in a fieldset; applies
  to fields that use multiple controls, like radios, checkboxes, multi-button controls;
  can either be a Boolean or a function that takes field options and returns a Boolean
- showIfOptions: optional; a function that returns the dropdown options when selecting the
  field as a condition
- getDataForCondition: optional; a function that takes the current value of the field and
  returns a list that can be compared with the stored condition of another field. its logic
  must match the corresponding ``get_data_for_condition`` method in the backend field class
*/

const fieldRegistry = {
  label: {
    title: Translate.string('Label', 'Classification'),
    inputComponent: LabelInput,
    noRequired: true,
    noRetentionPeriod: true,
    noLabel: true,
    icon: 'tag',
    customFormItem: true,
  },
  text: {
    title: Translate.string('Text field'),
    inputComponent: TextInput,
    settingsComponent: TextSettings,
    settingsFormValidator: textSettingsFormValidator,
    icon: 'textfield',
  },
  textarea: {
    title: Translate.string('Text area'),
    inputComponent: TextAreaInput,
    settingsComponent: TextAreaSettings,
    icon: 'textarea',
  },
  number: {
    title: Translate.string('Number'),
    inputComponent: NumberInput,
    settingsComponent: NumberSettings,
    settingsFormValidator: numberSettingsFormValidator,
    hasPrice: true,
    icon: 'seven-segment9',
  },
  checkbox: {
    title: Translate.string('Checkbox'),
    inputComponent: CheckboxInput,
    settingsComponent: CheckboxSettings,
    noLabel: true,
    hasPrice: true,
    icon: 'checkbox-checked',
    customFormItem: true,
    showIfOptions: checkboxShowIfOptions,
    getDataForCondition: checkboxGetDataForCondition,
  },
  date: {
    title: Translate.string('Date'),
    inputComponent: DateInput,
    settingsComponent: DateSettings,
    settingsFormDecorators: [dateSettingsFormDecorator],
    settingsFormInitialData: dateSettingsInitialData,
    icon: 'calendar',
  },
  bool: {
    title: Translate.string('Yes/No'),
    inputComponent: BooleanInput,
    settingsComponent: BooleanSettings,
    hasPrice: true,
    icon: 'switchon',
    renderAsFieldset: true,
    showIfOptions: booleanShowIfOptions,
    getDataForCondition: booleanGetDataForCondition,
  },
  phone: {
    title: Translate.string('Phone'),
    inputComponent: PhoneInput,
    icon: 'phone',
  },
  country: {
    title: Translate.string('Country'),
    inputComponent: CountryInput,
    settingsComponent: CountrySettings,
    icon: 'earth',
  },
  file: {
    title: Translate.string('File'),
    inputComponent: FileInput,
    icon: 'upload',
    renderAsFieldset: true,
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
    settingsFormDecorators: [choiceFieldsSettingsFormDecorator, singleChoiceSettingsFormDecorator],
    settingsFormInitialData: singleChoiceSettingsInitialData,
    showIfOptions: singleChoiceShowIfOptions,
    getDataForCondition: singleChoiceGetDataForCondition,
    icon: 'dropmenu',
    renderAsFieldset: options => options.itemType === 'radiogroup',
  },
  multi_choice: {
    title: Translate.string('Multiple Choice'),
    inputComponent: MultiChoiceInput,
    settingsComponent: MultiChoiceSettings,
    settingsModalSize: 'small',
    settingsFormDecorators: [choiceFieldsSettingsFormDecorator],
    settingsFormInitialData: multiChoiceSettingsInitialData,
    showIfOptions: multiChoiceShowIfOptions,
    getDataForCondition: multiChoiceGetDataForCondition,
    icon: 'list',
    renderAsFieldset: true,
  },
  accommodation: {
    title: Translate.string('Accommodation'),
    inputComponent: AccommodationInput,
    settingsComponent: AccommodationSettings,
    settingsModalSize: 'small',
    settingsFormDecorators: [choiceFieldsSettingsFormDecorator],
    settingsFormInitialData: accommodationSettingsInitialData,
    settingsFormValidator: accommodationSettingsFormValidator,
    noRequired: true,
    alwaysRequired: true,
    icon: 'home',
    renderAsFieldset: true,
    showIfOptions: accommodationShowIfOptions,
    getDataForCondition: accommodationGetDataForCondition,
  },
  accompanying_persons: {
    title: Translate.string('Accompanying Persons'),
    inputComponent: AccompanyingPersonsInput,
    settingsComponent: AccompanyingPersonsSettings,
    settingsFormInitialData: accompanyingPersonsSettingsInitialData,
    settingsModalSize: 'tiny',
    noRequired: true,
    hasPrice: true,
    icon: 'user',
    renderAsFieldset: true,
  },
  picture: {
    title: Translate.string('Picture'),
    inputComponent: PictureInput,
    icon: 'image',
    settingsComponent: PictureSettings,
    renderAsFieldset: true,
  },
  sessions: {
    title: Translate.string('Timetable Sessions'),
    inputComponent: TimetableSessionsInput,
    settingsComponent: TimetableSessionsSettings,
    settingsFormInitialData: timetableSessionsSettingsInitialData,
    settingsFormValidator: sessionsSettingsFormValidator,
    noRequired: true,
    hasPrice: false,
    icon: 'calendar-day',
    renderAsFieldset: true,
  },
};

export function getFieldRegistry() {
  const pluginFields = Object.fromEntries(
    getPluginObjects('regformCustomFields').map(({name, ...rest}) => [name, rest])
  );
  if (
    Object.entries(pluginFields).some(
      ([name, data]) =>
        !name.startsWith('ext__') && !(data.unsafeOverrideField && fieldRegistry[name])
    )
  ) {
    throw new Error(
      'Field names from plugins must begin with `ext__` or match an existing field name and set ' +
        'the `unsafeOverrideField` property to true'
    );
  }
  return {...fieldRegistry, ...pluginFields};
}
