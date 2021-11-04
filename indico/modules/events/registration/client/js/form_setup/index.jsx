// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import reducers from './reducers';
import RegistrationFormSetup from './RegistrationFormSetup';

export default function setupRegformSetup(root) {
  const {eventId, regformId, sections} = root.dataset;

  const initialData = {
    staticData: {
      eventId: parseInt(eventId, 10),
      regformId: parseInt(regformId, 10),
    },
    sections: JSON.parse(sections),
  };
  const store = createReduxStore('regform-setup', reducers, initialData);

  ReactDOM.render(
    <Provider store={store}>
      <RegistrationFormSetup />
    </Provider>,
    root
  );
}
