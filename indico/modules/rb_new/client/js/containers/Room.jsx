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

import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';

import Room from '../components/Room';
import {selectors as configSelectors} from '../common/config';
import {actions as userActions, selectors as userSelectors} from '../common/user';


export default connect(
    () => {
        const isFavoriteRoom = userSelectors.makeIsFavoriteRoom();
        return (state, props) => ({
            isFavorite: isFavoriteRoom(state, props),
            roomsSpriteToken: configSelectors.getRoomsSpriteToken(state),
        });
    },
    dispatch => bindActionCreators({
        addFavoriteRoom: userActions.addFavoriteRoom,
        delFavoriteRoom: userActions.delFavoriteRoom,
    }, dispatch)
)(Room);
