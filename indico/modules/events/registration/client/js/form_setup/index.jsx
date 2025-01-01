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
import RegistrationFormSetup from './RegistrationFormSetup';

export default function setupRegformSetup(root) {
  const {
    eventId,
    eventStartDate,
    eventEndDate,
    regformId,
    currency,
    dataRetentionRange,
    hasPredefinedAffiliations,
    formData,
  } = root.dataset;

  const initialData = {
    staticData: {
      eventId: parseInt(eventId, 10),
      regformId: parseInt(regformId, 10),
      hasPredefinedAffiliations: JSON.parse(hasPredefinedAffiliations),
      eventStartDate,
      eventEndDate,
      currency,
      dataRetentionRange: JSON.parse(dataRetentionRange),
    },
  };
  const store = createReduxStore('regform-setup', reducers, initialData);
  store.dispatch(setFormData(JSON.parse(formData)));

  ReactDOM.render(
    <Provider store={store}>
      <RegistrationFormSetup />
    </Provider>,
    root
  );
}
