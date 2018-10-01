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

import _ from 'lodash';
import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';


export const hasLoadedEquipmentTypes = ({rooms}) => rooms.requests.equipmentTypes.state === RequestState.SUCCESS;
export const getEquipmentTypes = ({rooms}) => rooms.equipmentTypes;

export const getAllRooms = ({rooms}) => rooms.rooms;
export const hasLoadedRooms = ({rooms}) => rooms.requests.rooms.state === RequestState.SUCCESS;
export const getRoom = (state, {roomId}) => getAllRooms(state)[roomId];

const getAllAvailabilities = ({rooms}) => rooms.availability;
export const isFetchingAvailability = ({rooms}) => rooms.requests.availability.state === RequestState.STARTED;
export const getAvailability = (state, {roomId}) => getAllAvailabilities(state)[roomId];

const getAllAttributes = ({rooms}) => rooms.attributes;
export const isFetchingAttributes = ({rooms}) => rooms.requests.attributes.state === RequestState.STARTED;
export const getAttributes = (state, {roomId}) => getAllAttributes(state)[roomId];

export const hasDetails = createSelector(
    getAvailability,
    getAttributes,
    (...details) => details.every(x => x !== undefined)
);

export const getBuildings = createSelector(
    getAllRooms,
    (allRooms) => {
        const roomsByBuilding = {};
        Object.values(allRooms).forEach((room) => {
            if (!roomsByBuilding.hasOwnProperty(room.building)) {
                roomsByBuilding[room.building] = [];
            }
            roomsByBuilding[room.building].push(room);
        });
        return Object.entries(roomsByBuilding).reduce((obj, [building, rooms]) => {
            const data = {
                rooms,
                floors: _.sortedUniq(rooms.map(r => r.floor).sort()),
                number: building,
            };
            return {...obj, [building]: data};
        }, {});
    }
);
