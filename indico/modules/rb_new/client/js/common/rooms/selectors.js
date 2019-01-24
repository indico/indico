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
import {getAllUserRoomPermissions} from '../user/selectors';


export const hasLoadedEquipmentTypes = ({rooms}) => rooms.requests.equipmentTypes.state === RequestState.SUCCESS;
const getEquipmentTypes = ({rooms}) => rooms.equipmentTypes;
const getFeaturesMapping = createSelector(
    getEquipmentTypes,
    equipmentTypes => {
        const features = {};
        equipmentTypes.forEach(({name: eqName, features: eqFeatures}) => {
            eqFeatures.forEach(feature => {
                if (!(feature.name in features)) {
                    features[feature.name] = {
                        ...feature,
                        equipment: []
                    };
                }
                features[feature.name].equipment.push(eqName);
            });
        });
        return features;
    }
);
/** Get equipment type names except those with an 1:1 mapping to a feature */
export const getEquipmentTypeNamesWithoutFeatures = createSelector(
    getEquipmentTypes,
    getFeaturesMapping,
    (equipmentTypes, features) => {
        return equipmentTypes
            .filter(eq => eq.features.every(f => features[f.name].equipment.length > 1))
            .map(eq => eq.name)
            .sort();
    }
);
/** Get all available room features */
export const getFeatures = createSelector(
    getFeaturesMapping,
    features => {
        features = Object.values(features).map(f => _.pick(f, ['icon', 'name', 'title']));
        return _.sortBy(features, 'title');
    }
);

export const getAllRooms = createSelector(
    ({rooms}) => rooms.rooms,
    getEquipmentTypes,
    getAllUserRoomPermissions,
    (rawRooms, equipmentTypes, allUserPermissions) => {
        equipmentTypes = equipmentTypes.reduce((obj, eq) => ({...obj, [eq.id]: eq}), {});
        return _.fromPairs(rawRooms.map(room => {
            const {availableEquipment: equipment, ...roomData} = room;
            // gather a list of features the room has based on its equipment
            const features = {};
            equipment.map(id => equipmentTypes[id]).forEach(equipmentType => {
                equipmentType.features.forEach(({id, ...feature}) => {
                    if (!(id in features)) {
                        features[id] = {
                            ...feature,
                            equipment: [],
                        };
                    }
                    features[id].equipment.push(equipmentType.name);
                });
            });
            const sortedFeatures = _.sortBy(Object.values(features), 'title');
            sortedFeatures.forEach(f => f.equipment.sort());
            const permissions = allUserPermissions[room.id] || {book: false, prebook: false, override: false};
            return [room.id, {
                ...roomData,
                equipment: equipment.map(id => equipmentTypes[id].name).sort(),
                features: sortedFeatures,
                canUserBook: permissions.book,
                canUserPrebook: permissions.prebook,
                canUserOverride: permissions.override,
            }];
        }));
    }
);

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
    allRooms => {
        const buildings = new Set(Object.values(allRooms).map(room => room.building));
        return Array.from(buildings).sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
    }
);
