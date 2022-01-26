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

import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import FormSection from '../form/FormSection';
import {getItems, getNestedSections, getStaticData} from '../form/selectors';

import {getUserInfo, getUpdateMode} from './selectors';

import '../../styles/regform.module.scss';

export default function RegistrationFormSubmission() {
  const items = useSelector(getItems);
  const sections = useSelector(getNestedSections);
  const userInfo = useSelector(getUserInfo);
  const {submitUrl, registrationData} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);

  const onSubmit = async data => {
    console.log(data);
    let resp;
    try {
      resp = await indicoAxios.post(submitUrl, data);
    } catch (err) {
      return handleSubmitError(err);
    }

    if (resp.data.redirect) {
      location.href = resp.data.redirect;
    }
  };

  const initialValues = Object.fromEntries(
    Object.entries(userInfo).filter(([key]) => {
      return Object.values(items).some(
        ({htmlName, fieldIsPersonalData, isEnabled}) =>
          htmlName === key && fieldIsPersonalData && isEnabled
      );
    })
  );

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={isUpdateMode ? registrationData : initialValues}
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
            label={Translate.string(isUpdateMode ? 'Modify' : 'Register')}
          />
        </form>
      )}
    </FinalForm>
  );
}
