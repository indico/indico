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
import {push as pushRoute} from 'connected-react-router';
import UserActions from '../components/UserActions';

import {selectors as userSelectors} from '../common/user';
import {actions as blockingsActions} from '../modules/blockings';
import * as globalActions from '../actions';


export default connect(
    state => ({
        isAdmin: userSelectors.isUserAdmin(state),
        hasOwnedRooms: userSelectors.hasOwnedRooms(state),
    }),
    dispatch => ({
        gotoMyRoomsList() {
            dispatch(globalActions.setFilterParameter('roomList', 'onlyMine', true));
            dispatch(pushRoute('/rooms?mine=true'));
        },
        gotoMyBlockings() {
            dispatch(blockingsActions.setFilterParameter('myBlockings', true));
            dispatch(pushRoute('/blockings?myBlockings=true'));
        },
    })
)(UserActions);
