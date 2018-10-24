import ReactDOM from 'react-dom';
import React from 'react';
import {Provider} from 'react-redux';

import Overridable from 'indico/react/util/Overridable';
import setupUserMenu from 'indico/react/containers/UserMenu';
import App from './components/App';

import createRBStore, {history} from './store';
import {init} from './actions';
import {selectors as configSelectors} from './common/config';
import {selectors as userSelectors} from './common/user';

import 'semantic-ui-css/semantic.css';
import '../styles/main.scss';


export default function setup(overrides = {}, postReducers = []) {
    document.addEventListener('DOMContentLoaded', () => {
        const appContainer = document.getElementById('rb-app-container');
        const store = createRBStore(overrides, postReducers);

        store.dispatch(init());
        setupUserMenu(
            document.getElementById('indico-user-menu-container'), store,
            userSelectors.getUserInfo, configSelectors.getLanguages
        );

        ReactDOM.render(
            <Provider store={store}>
                <Overridable id="App">
                    <App history={history} />
                </Overridable>
            </Provider>,
            appContainer
        );
    });
}
