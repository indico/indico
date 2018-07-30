/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import '@babel/polyfill';
import ReactDOM from 'react-dom';
import React from 'react';
import {Provider} from 'react-redux';

import moment from 'moment';
import 'semantic-ui-css/semantic.css';
import '../styles/main.scss';

import setupUserMenu from 'indico/react/containers/UserMenu';
import App from './containers/App';

import createRBStore, {history} from './store';


document.addEventListener('DOMContentLoaded', () => {
    moment.locale(Indico.User.language);

    const appContainer = document.getElementById('rb-app-container');
    const store = createRBStore({
        user: {
            firstName: Indico.User.first_name,
            lastName: Indico.User.last_name,
            email: Indico.User.email,
            avatarBgColor: Indico.User.avatar_bg_color,
            language: Indico.User.language,
            isAdmin: Indico.User.is_admin,
            favoriteRooms: {},
            hasOwnedRooms: false,
        },
        staticData: {
            availableLanguages: Indico.Settings.Languages,
            tileServerURL: Indico.Settings.TileServerURL
        }
    });

    store.dispatch({type: 'INIT'});
    setupUserMenu(document.getElementById('indico-user-menu-container'), store);

    ReactDOM.render(
        <Provider store={store}>
            <App history={history} />
        </Provider>,
        appContainer
    );
});
