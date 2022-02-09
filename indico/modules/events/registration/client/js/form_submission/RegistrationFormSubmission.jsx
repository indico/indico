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
import {Message} from 'semantic-ui-react';

import {FinalSubmitButton, handleSubmitError, FinalCheckbox} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import FormSection from '../form/FormSection';
import {getItems, getNestedSections, getStaticData} from '../form/selectors';

import {getUserInfo, getUpdateMode, getModeration, getManagement} from './selectors';

import '../../styles/regform.module.scss';

/**
 * The registration Marshmallow schema does not allow
 * unknown fields so we remove disabled personal data fields from the
 * form initial values.
 */
function getInitialValues(userInfo, items) {
  return Object.fromEntries(
    Object.entries(userInfo).filter(([key]) => {
      return Object.values(items).some(
        ({htmlName, fieldIsPersonalData, isEnabled}) =>
          htmlName === key && fieldIsPersonalData && isEnabled
      );
    })
  );
}

function EmailNotification() {
  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Email notifications</Translate>
      </Message.Header>
      <div style={{marginTop: 10}}>
        <FinalCheckbox
          label={Translate.string('Send an email notification to the user')}
          name="notify_user"
          toggle
        />
      </div>
    </Message>
  );
}

export default function RegistrationFormSubmission() {
  const items = useSelector(getItems);
  const sections = useSelector(getNestedSections);
  const userInfo = useSelector(getUserInfo);
  const {submitUrl, registrationData} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const isModerated = useSelector(getModeration);
  const isManagement = useSelector(getManagement);

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

  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={isUpdateMode ? registrationData : getInitialValues(userInfo, items)}
      initialValuesEqual={_.isEqual}
      subscription={{}}
    >
      {fprops => (
        <form onSubmit={fprops.handleSubmit}>
          {sections.map(section => (
            <FormSection key={section.id} {...section} />
          ))}
          <div>
            {isManagement && <EmailNotification />}
            <FinalSubmitButton
              disabledUntilChange={false}
              disabledIfInvalid={false}
              label={
                isUpdateMode
                  ? Translate.string('Modify')
                  : isModerated
                  ? Translate.string('Apply')
                  : Translate.string('Register')
              }
              style={{
                marginTop: 20,
                textAlign: 'right',
              }}
            />
          </div>
        </form>
      )}
    </FinalForm>
  );
}
