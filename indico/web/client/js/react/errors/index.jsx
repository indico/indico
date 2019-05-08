// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';
import {addError} from './actions';
import reducer from './reducers';
import ErrorDialog from './container';


let store;
export default function showReactErrorDialog(error) {
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
}
