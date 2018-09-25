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
import {connect} from 'react-redux';

import App from '../components/App';
import {fetchMapAspects, resetPageState} from '../actions';
import {history} from '../store';
import {actions as configActions} from '../common/config';
import {actions as roomsActions} from '../common/rooms';
import {actions as userActions} from '../common/user';
import * as selectors from '../selectors';


export default connect(
    state => ({
        filtersSet: !!history.location.search || !!state.bookRoom.filters.recurrence.type,
        isInitializing: selectors.isInitializing(state),
    }),
    dispatch => ({
        fetchInitialData() {
            dispatch(configActions.fetchConfig()).then(() => {
                // we only need map aspects if the map is enabled, which depends on the config
                dispatch(fetchMapAspects());
            });
            dispatch(userActions.fetchUserInfo());
            dispatch(userActions.fetchFavoriteRooms());
            dispatch(roomsActions.fetchEquipmentTypes());
            dispatch(roomsActions.fetchRooms());
        },
        resetPageState(namespace) {
            dispatch(resetPageState(namespace));
        }
    })
)(App);
