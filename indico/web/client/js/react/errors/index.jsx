// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

// eslint-disable-next-line import/no-cycle
import createReduxStore from 'indico/utils/redux';
import {addError, showReportForm} from './actions';
import reducer from './reducers';
import ErrorDialog from './container';

let store;
export default function showReactErrorDialog(error, instantReport = false) {
  if (!store) {
    store = createReduxStore('errors', {
      errors: reducer,
    });
    const container = document.createElement('div');
    document.body.appendChild(container);
    const jsx = (
      <Provider store={store}>
        <ErrorDialog initialValues={{email: Indico.User.email}} />
      </Provider>
    );
    ReactDOM.render(jsx, container);
  }
  store.dispatch(addError(error));
  if (instantReport) {
    store.dispatch(showReportForm());
  }
}
