// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

const makeSorter = attr => (a, b) => a[attr].localeCompare(b[attr]);

const _getAllLocations = ({admin}) => admin.locations;
const _getAllRooms = ({admin}) => admin.rooms;
export const getAllLocations = createSelector(
  _getAllLocations,
  _getAllRooms,
  (locations, rooms) => {
    return locations.sort(makeSorter('name')).map(loc => ({
      ...loc,
      numRooms: rooms.filter(room => room.locationId === loc.id).length,
    }));
  }
);
export const getLocation = createSelector(
  _getAllLocations,
  _getAllRooms,
  (state, {locationId}) => locationId,
  (locations, rooms, locationId) => {
    const location = locations.find(x => x.id === locationId);
    if (!location) {
      return null;
    }
    return {
      ...location,
      rooms: rooms.filter(room => room.locationId === location.id),
    };
  }
);

const _isFetchingLocations = ({admin}) =>
  admin.requests.locations.state === RequestState.STARTED && !admin.requests.locations.reloading;
const _isFetchingRooms = ({admin}) =>
  admin.requests.rooms.state === RequestState.STARTED && !admin.requests.rooms.reloading;
export const isFetchingLocations = state => _isFetchingLocations(state) || _isFetchingRooms(state);
export const getFilters = ({admin}) => admin.filters;

export const _getEquipmentTypes = ({admin}) => admin.equipmentTypes;
export const _getFeatures = ({admin}) => admin.features;
const _getFeaturesMap = createSelector(
  _getFeatures,
  features => _.fromPairs(features.map(feat => [feat.id, feat]))
);

export const getEquipmentTypes = createSelector(
  _getEquipmentTypes,
  _getFeaturesMap,
  (equipmentTypes, featuresMap) => {
    return equipmentTypes
      .map(eq => ({
        ...eq,
        features: eq.features.map(id => featuresMap[id]).sort(makeSorter('title')),
      }))
      .sort(makeSorter('name'));
  }
);

export const getFeatures = createSelector(
  _getEquipmentTypes,
  _getFeatures,
  (equipmentTypes, features) => {
    return features
      .map(feat => ({
        ...feat,
        numEquipmentTypes: equipmentTypes.filter(eq => eq.features.includes(feat.id)).length,
      }))
      .sort(makeSorter('title'));
  }
);

export const isFetchingFeaturesOrEquipmentTypes = ({admin}) =>
  admin.requests.equipmentTypes.state === RequestState.STARTED ||
  admin.requests.features.state === RequestState.STARTED;

export const isFetchingAttributes = ({admin}) =>
  admin.requests.attributes.state === RequestState.STARTED;

export const _getAttributes = ({admin}) => admin.attributes;
export const getAttributes = createSelector(
  _getAttributes,
  attributes => attributes.slice().sort(makeSorter('title'))
);

export const hasSettingsLoaded = ({admin}) =>
  admin.requests.settings.state === RequestState.SUCCESS;
export const getSettings = ({admin}) => admin.settings;
