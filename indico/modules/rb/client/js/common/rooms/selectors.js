// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

import {canManagersEditRooms} from '../config/selectors';
import {getAllUserRoomPermissions, isUserRBAdmin} from '../user/selectors';

export const hasLoadedEquipmentTypes = ({rooms}) =>
  rooms.requests.equipmentTypes.state === RequestState.SUCCESS ||
  rooms.requests.equipmentTypes.reloading;
export const getAllEquipmentTypes = ({rooms}) => rooms.equipmentTypes;
const getUsedEquipmentTypes = createSelector(
  getAllEquipmentTypes,
  equipmentTypes => equipmentTypes.filter(x => x.used)
);
const getFeaturesMapping = createSelector(
  getUsedEquipmentTypes,
  equipmentTypes => {
    const features = {};
    equipmentTypes.forEach(({name: eqName, features: eqFeatures}) => {
      eqFeatures.forEach(feature => {
        if (!(feature.name in features)) {
          features[feature.name] = {
            ...feature,
            equipment: [],
          };
        }
        features[feature.name].equipment.push(eqName);
      });
    });
    return features;
  }
);
/** Get equipment type names except those with an 1:1 mapping to a feature */
export const getUsedEquipmentTypeNamesWithoutFeatures = createSelector(
  getUsedEquipmentTypes,
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
  getAllEquipmentTypes,
  getAllUserRoomPermissions,
  isUserRBAdmin,
  canManagersEditRooms,
  (rawRooms, equipmentTypes, allUserPermissions, isRBAdmin, managersEditRooms) => {
    equipmentTypes = equipmentTypes.reduce((obj, eq) => ({...obj, [eq.id]: eq}), {});
    return _.fromPairs(
      rawRooms.map(room => {
        const {availableEquipment: equipment, ...roomData} = room;
        // gather a list of features the room has based on its equipment
        const features = {};
        equipment
          .map(id => equipmentTypes[id])
          .forEach(equipmentType => {
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
        const permissions = allUserPermissions[room.id] || {
          book: false,
          prebook: false,
          override: false,
          manage: false,
        };
        return [
          room.id,
          {
            ...roomData,
            equipment: equipment.map(id => equipmentTypes[id].name).sort(),
            features: sortedFeatures,
            canUserEdit: permissions.manage && (isRBAdmin || managersEditRooms),
            canUserBook: permissions.book,
            canUserPrebook: permissions.prebook,
            canUserOverride: permissions.override,
          },
        ];
      })
    );
  }
);

export const hasLoadedRooms = ({rooms}) =>
  rooms.requests.rooms.state === RequestState.SUCCESS || rooms.requests.rooms.reloading;
export const getRoom = (state, {roomId}) => getAllRooms(state)[roomId];

const getAllAvailabilities = ({rooms}) => rooms.availability;
export const isFetchingAvailability = ({rooms}) =>
  rooms.requests.availability.state === RequestState.STARTED;
export const getAvailability = (state, {roomId}) => getAllAvailabilities(state)[roomId];

const getAllAttributes = ({rooms}) => rooms.attributes;
export const isFetchingAttributes = ({rooms}) =>
  rooms.requests.attributes.state === RequestState.STARTED;
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
