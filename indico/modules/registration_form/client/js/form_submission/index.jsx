// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import {setFormData} from './actions';
import reducers from './reducers';
import RegistrationFormSubmission from './RegistrationFormSubmission';

export default function setupRegformSubmission(root) {
  const {
    eventId,
    regformId,
    currency,
    management,
    paid,
    moderated = false,
    lockEmail = false,
    submitUrl,
    formData,
    initialValues = null,
    registrationData = null,
    registrationUuid = null,
    fileData = null,
    publishToParticipants,
    publishToPublic,
    consentToPublish = null,
    policyAgreementRequired,
    captchaRequired = false,
    captchaSettings = null,
    ...extraData
  } = root.dataset;

  const initialData = {
    staticData: {
      eventId: parseInt(eventId, 10),
      regformId: parseInt(regformId, 10),
      management: JSON.parse(management),
      paid: paid ? JSON.parse(paid) : false,
      moderated: JSON.parse(moderated),
      lockEmail: JSON.parse(lockEmail),
      initialValues: JSON.parse(initialValues),
      submitUrl,
      registrationData: registrationData
        ? {...JSON.parse(registrationData), consent_to_publish: consentToPublish}
        : {},
      registrationUuid,
      fileData: fileData ? JSON.parse(fileData) : {},
      currency,
      publishToParticipants,
      publishToPublic,
      policyAgreementRequired: JSON.parse(policyAgreementRequired),
      captchaRequired: JSON.parse(captchaRequired),
      captchaSettings: JSON.parse(captchaSettings),
      // XXX: do NOT use extraData for anything in the core; this is solely meant as a way to
      // pass data to plugins injecting custom stuff in the registration form. if you add
      // something in the core, handle it properly above!
      extraData,
    },
  };
  const store = createReduxStore('regform-submission', reducers, initialData);
  store.dispatch(setFormData(JSON.parse(formData)));

  ReactDOM.render(
    <Provider store={store}>
      <RegistrationFormSubmission />
    </Provider>,
    root
  );
}
