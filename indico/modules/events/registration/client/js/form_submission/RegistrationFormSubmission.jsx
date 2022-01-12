// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useSelector} from 'react-redux';

import FormSection from '../form/FormSection';

import {getNestedSections} from './selectors';

import '../../styles/regform.module.scss';

export default function RegistrationFormSubmission() {
  const sections = useSelector(getNestedSections);

  return sections.map(section => <FormSection key={section.id} {...section} />);
}
