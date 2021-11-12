// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import InputLabel from './InputLabel';
import InputPhone from './InputPhone';
import InputText, {TextSettings} from './InputText';
import InputTextArea, {TextAreaSettings} from './InputTextArea';

/*
Available keys:
- title: required; used to show the field type when adding a new field
- inputComponent: required; the component used to render the field
- settingsComponent: optional; used if the field has custom settings
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
  textarea: {
    title: 'Text area',
    inputComponent: InputTextArea,
    settingsComponent: TextAreaSettings,
  },
  phone: {
    title: 'Phone',
    inputComponent: InputPhone,
  },
  // TODO add other input types
};
