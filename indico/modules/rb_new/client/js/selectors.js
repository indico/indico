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

import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';
import {selectors as roomsSelectors} from './common/rooms';


// TODO: move these to common/.../selectors.js
export const getRoomsSpriteToken = ({staticData}) => staticData.roomsSpriteToken;

const hasLoadedUserInfo = ({user}) => user.requests.info.state === RequestState.SUCCESS;
export const getUserInfo = ({user}) => user.info;
export const isUserAdmin = state => getUserInfo(state).isAdmin;
export const hasOwnedRooms = state => getUserInfo(state).hasOwnedRooms;
export const getFavoriteRooms = ({user}) => user.favorites;
export const hasFavoriteRooms = createSelector(
    getFavoriteRooms,
    favoriteRooms => Object.values(favoriteRooms).some(fr => fr),
);
export const makeIsFavoriteRoom = () => createSelector(
    getFavoriteRooms,
    (state, {room}) => room.id,
    (favoriteRooms, roomId) => !!favoriteRooms[roomId]
);


const hasLoadedEquipmentTypes = ({equipment}) => equipment.request.state === RequestState.SUCCESS;
export const getEquipmentTypes = ({equipment}) => equipment.types;

export const isInitializing = createSelector(
    hasLoadedUserInfo,
    roomsSelectors.hasLoadedRooms,
    hasLoadedEquipmentTypes,
    (...ready) => ready.some(x => !x)
);
