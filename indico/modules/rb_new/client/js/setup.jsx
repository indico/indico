import ReactDOM from 'react-dom';
import React from 'react';
import {Provider} from 'react-redux';

import setupUserMenu from 'indico/react/containers/UserMenu';
import App from './components/App';

import createRBStore, {history} from './store';
import {init} from './actions';
import {selectors as configSelectors} from './common/config';
import {selectors as userSelectors, actions as userActions} from './common/user';
import {actions as roomsActions} from './common/rooms';

import 'indico-sui-theme/semantic.css';
import '../styles/main.scss';


export default function setup(overrides = {}, postReducers = []) {
    document.addEventListener('DOMContentLoaded', () => {
        const appContainer = document.getElementById('rb-app-container');
        const store = createRBStore(overrides, postReducers);

        let oldPath = history.location.pathname;
        history.listen(({pathname: newPath}) => {
            if (oldPath.startsWith('/admin') && !newPath.startsWith('/admin')) {
                // user left the admin area so we need to reload some data that might have been changed
                // TODO: add more things here once admins can change them (e.g. map areas)
                store.dispatch(roomsActions.fetchEquipmentTypes());
                store.dispatch(roomsActions.fetchRooms());
                store.dispatch(userActions.fetchAllRoomPermissions());
            }
            oldPath = newPath;
        });

        store.dispatch(init());
        setupUserMenu(
            document.getElementById('indico-user-menu-container'), store,
            userSelectors.getUserInfo, configSelectors.getLanguages
        );

        ReactDOM.render(
            <Provider store={store}>
                <App history={history} />
            </Provider>,
            appContainer
        );
    });
}
