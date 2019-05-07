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


export const hasLoadedUserInfo = ({user}) => user.requests.info.state === RequestState.SUCCESS;
export const getUserInfo = ({user}) => user.info;
export const isUserRBAdmin = state => getUserInfo(state).isRBAdmin;
export const isUserAdmin = state => getUserInfo(state).isAdmin;
export const isUserAdminOverrideEnabled = state => getUserInfo(state).isAdminOverrideEnabled;
export const hasOwnedRooms = state => getUserInfo(state).hasOwnedRooms;
export const getRealUserRoomPermissions = ({user}) => user.roomPermissions;
export const isCheckingUserRoomPermissions = ({user}) => user.requests.roomPermissions.state === RequestState.STARTED;

export const getAllUserRoomPermissions = createSelector(
    getRealUserRoomPermissions,
    isUserAdminOverrideEnabled,
    (permissions, override) => {
        if (!permissions) {
            // not loaded yet
            return {};
        }
        return (override && permissions.admin) ? permissions.admin : permissions.user;
    }
);

export const getUnbookableRoomIds = createSelector(
    getAllUserRoomPermissions,
    permissions => Object.entries(permissions).filter(([, perms]) => !perms.book && !perms.prebook).map(([id]) => +id)
);

export const getManagedRoomIds = createSelector(
    getAllUserRoomPermissions,
    permissions => Object.entries(permissions).filter(([, perms]) => perms.manage).map(([id]) => +id)
);

export const hasUnbookableRooms = createSelector(
    getUnbookableRoomIds,
    unbookableRoomIds => !!unbookableRoomIds.length
);

const getFavoriteRooms = ({user}) => user.favorites;
export const hasFavoriteRooms = createSelector(
    getFavoriteRooms,
    favoriteRooms => Object.values(favoriteRooms).some(fr => fr),
);
export const makeIsFavoriteRoom = () => createSelector(
    getFavoriteRooms,
    (state, {room}) => room.id,
    (favoriteRooms, roomId) => !!favoriteRooms[roomId]
);
