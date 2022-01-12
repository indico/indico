// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';

import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import FormSection from '../form/FormSection';

import {getNestedSections, getUserInfo} from './selectors';

import '../../styles/regform.module.scss';

export default function RegistrationFormSubmission() {
  const sections = useSelector(getNestedSections);
  const userInfo = useSelector(getUserInfo);

  const onSubmit = async data => {
    console.log(data);
    await new Promise(r => setTimeout(r, 2500));
  };

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={userInfo}
      initialValuesEqual={_.isEqual}
      subscription={{}}
    >
      {fprops => (
        <form onSubmit={fprops.handleSubmit}>
          {sections.map(section => (
            <FormSection key={section.id} {...section} />
          ))}
          <FinalSubmitButton
            disabledUntilChange={false}
            // TODO: use different label when modifying registration
            label={Translate.string('Register')}
          />
        </form>
      )}
    </FinalForm>
  );
}
