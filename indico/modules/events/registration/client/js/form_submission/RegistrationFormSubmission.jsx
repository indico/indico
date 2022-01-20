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
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import FormSection from '../form/FormSection';

import {getNestedSections, getUserInfo, getStaticData} from './selectors';

import '../../styles/regform.module.scss';

export default function RegistrationFormSubmission() {
  const sections = useSelector(getNestedSections);
  const userInfo = useSelector(getUserInfo);
  const {csrfToken, submitUrl} = useSelector(getStaticData);

  const onSubmit = async data => {
    data = {...data, csrf_token: csrfToken};
    console.log(data);
    try {
      await indicoAxios.post(submitUrl, data);
    } catch (err) {
      handleAxiosError(err);
    }
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
            disabledIfInvalid={false}
            // TODO: use different label when modifying registration
            label={Translate.string('Register')}
          />
        </form>
      )}
    </FinalForm>
  );
}
