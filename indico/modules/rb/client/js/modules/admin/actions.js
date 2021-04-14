// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import attributesURL from 'indico-url:rb.admin_attributes';
import equipmentTypesURL from 'indico-url:rb.admin_equipment_types';
import featuresURL from 'indico-url:rb.admin_features';
import locationsURL from 'indico-url:rb.admin_locations';
import roomURL from 'indico-url:rb.admin_room';
import roomsURL from 'indico-url:rb.admin_rooms';
import settingsURL from 'indico-url:rb.admin_settings';

import _ from 'lodash';

import {indicoAxios} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';

import {actions as filtersActions} from '../../common/filters';

export const FETCH_SETTINGS_REQUEST = 'admin/FETCH_SETTINGS_REQUEST';
export const FETCH_SETTINGS_SUCCESS = 'admin/FETCH_SETTINGS_SUCCESS';
export const FETCH_SETTINGS_ERROR = 'admin/FETCH_SETTINGS_ERROR';
export const SETTINGS_RECEIVED = 'admin/SETTINGS_RECEIVED';

export const FETCH_LOCATIONS_REQUEST = 'admin/FETCH_LOCATIONS_REQUEST';
export const FETCH_LOCATIONS_SUCCESS = 'admin/FETCH_LOCATIONS_SUCCESS';
export const FETCH_LOCATIONS_ERROR = 'admin/FETCH_LOCATIONS_ERROR';
export const LOCATIONS_RECEIVED = 'admin/LOCATIONS_RECEIVED';
export const LOCATION_RECEIVED = 'admin/LOCATION_RECEIVED';
export const LOCATION_DELETED = 'admin/LOCATION_DELETED';

export const FETCH_ROOMS_REQUEST = 'admin/FETCH_ROOMS_REQUEST';
export const FETCH_ROOMS_SUCCESS = 'admin/FETCH_ROOMS_SUCCESS';
export const FETCH_ROOMS_ERROR = 'admin/FETCH_ROOMS_ERROR';
export const ROOMS_RECEIVED = 'admin/ROOMS_RECEIVED';
export const ROOM_DELETED = 'admin/ROOM_DELETED';

export const FETCH_FEATURES_REQUEST = 'admin/FETCH_FEATURES_REQUEST';
export const FETCH_FEATURES_SUCCESS = 'admin/FETCH_FEATURES_SUCCESS';
export const FETCH_FEATURES_ERROR = 'admin/FETCH_FEATURES_ERROR';
export const FEATURES_RECEIVED = 'admin/FEATURES_RECEIVED';
export const FEATURE_RECEIVED = 'admin/FEATURE_RECEIVED';
export const FEATURE_DELETED = 'admin/FEATURE_DELETED';

export const FETCH_EQUIPMENT_TYPES_REQUEST = 'admin/FETCH_EQUIPMENT_TYPES_REQUEST';
export const FETCH_EQUIPMENT_TYPES_SUCCESS = 'admin/FETCH_EQUIPMENT_TYPES_SUCCESS';
export const FETCH_EQUIPMENT_TYPES_ERROR = 'admin/FETCH_EQUIPMENT_TYPES_ERROR';
export const EQUIPMENT_TYPES_RECEIVED = 'admin/EQUIPMENT_TYPES_RECEIVED';
export const EQUIPMENT_TYPE_RECEIVED = 'admin/EQUIPMENT_TYPE_RECEIVED';
export const EQUIPMENT_TYPE_DELETED = 'admin/EQUIPMENT_TYPE_DELETED';

export const FETCH_ATTRIBUTES_REQUEST = 'admin/FETCH_ATTRIBUTES_REQUEST';
export const FETCH_ATTRIBUTES_SUCCESS = 'admin/FETCH_ATTRIBUTES_SUCCESS';
export const FETCH_ATTRIBUTES_ERROR = 'admin/FETCH_ATTRIBUTES_ERROR';
export const ATTRIBUTES_RECEIVED = 'admin/ATTRIBUTES_RECEIVED';
export const ATTRIBUTE_RECEIVED = 'admin/ATTRIBUTE_RECEIVED';
export const ATTRIBUTE_DELETED = 'admin/ATTRIBUTE_DELETED';

export const FILTER_NAMESPACE = 'admin';

export function fetchSettings() {
  return ajaxAction(
    () => indicoAxios.get(settingsURL()),
    FETCH_SETTINGS_REQUEST,
    [SETTINGS_RECEIVED, FETCH_SETTINGS_SUCCESS],
    FETCH_SETTINGS_ERROR
  );
}

export function updateSettings(data) {
  return submitFormAction(() => indicoAxios.patch(settingsURL(), data), null, SETTINGS_RECEIVED);
}

export function fetchLocations() {
  return ajaxAction(
    () => indicoAxios.get(locationsURL()),
    FETCH_LOCATIONS_REQUEST,
    [LOCATIONS_RECEIVED, FETCH_LOCATIONS_SUCCESS],
    FETCH_LOCATIONS_ERROR
  );
}

export function fetchRooms() {
  return ajaxAction(
    () => indicoAxios.get(roomsURL()),
    FETCH_ROOMS_REQUEST,
    [ROOMS_RECEIVED, FETCH_ROOMS_SUCCESS],
    FETCH_ROOMS_ERROR
  );
}

export function fetchEquipmentTypes() {
  return ajaxAction(
    () => indicoAxios.get(equipmentTypesURL()),
    FETCH_EQUIPMENT_TYPES_REQUEST,
    [EQUIPMENT_TYPES_RECEIVED, FETCH_EQUIPMENT_TYPES_SUCCESS],
    FETCH_EQUIPMENT_TYPES_ERROR
  );
}

export function fetchFeatures() {
  return ajaxAction(
    () => indicoAxios.get(featuresURL()),
    FETCH_FEATURES_REQUEST,
    [FEATURES_RECEIVED, FETCH_FEATURES_SUCCESS],
    FETCH_FEATURES_ERROR
  );
}

export function fetchAttributes() {
  return ajaxAction(
    () => indicoAxios.get(attributesURL()),
    FETCH_ATTRIBUTES_REQUEST,
    [ATTRIBUTES_RECEIVED, FETCH_ATTRIBUTES_SUCCESS],
    FETCH_ATTRIBUTES_ERROR
  );
}

export function clearTextFilter() {
  return filtersActions.setFilterParameter(FILTER_NAMESPACE, 'text', null);
}

export function deleteEquipmentType(id) {
  return ajaxAction(
    () => indicoAxios.delete(equipmentTypesURL({equipment_type_id: id})),
    null,
    () => ({
      type: EQUIPMENT_TYPE_DELETED,
      id,
    })
  );
}

export function updateEquipmentType(id, data) {
  return submitFormAction(
    () => indicoAxios.patch(equipmentTypesURL({equipment_type_id: id}), data),
    null,
    EQUIPMENT_TYPE_RECEIVED
  );
}

export function createEquipmentType(data) {
  return submitFormAction(
    () => indicoAxios.post(equipmentTypesURL(), data),
    null,
    EQUIPMENT_TYPE_RECEIVED
  );
}

export function deleteFeature(id) {
  return ajaxAction(() => indicoAxios.delete(featuresURL({feature_id: id})), null, () => ({
    type: FEATURE_DELETED,
    id,
  }));
}

export function updateFeature(id, data) {
  return submitFormAction(
    () => indicoAxios.patch(featuresURL({feature_id: id}), data),
    null,
    FEATURE_RECEIVED
  );
}

export function createFeature(data) {
  return submitFormAction(() => indicoAxios.post(featuresURL(), data), null, FEATURE_RECEIVED);
}

export function deleteAttribute(id) {
  return ajaxAction(() => indicoAxios.delete(attributesURL({attribute_id: id})), null, () => ({
    type: ATTRIBUTE_DELETED,
    id,
  }));
}

export function updateAttribute(id, data) {
  return submitFormAction(
    () => indicoAxios.patch(attributesURL({attribute_id: id}), data),
    null,
    ATTRIBUTE_RECEIVED
  );
}

export function createAttribute(data) {
  return submitFormAction(() => indicoAxios.post(attributesURL(), data), null, ATTRIBUTE_RECEIVED);
}

export function deleteLocation(id) {
  return ajaxAction(() => indicoAxios.delete(locationsURL({location_id: id})), null, () => ({
    type: LOCATION_DELETED,
    id,
  }));
}

export function updateLocation(id, data) {
  return submitFormAction(
    () =>
      indicoAxios.patch(locationsURL({location_id: id}), _.omit(data, '_map_url_template_choice')),
    null,
    LOCATION_RECEIVED
  );
}

export function createLocation(data) {
  return submitFormAction(
    () => indicoAxios.post(locationsURL(), _.omit(data, '_map_url_template_choice')),
    null,
    LOCATION_RECEIVED
  );
}

export function deleteRoom(id) {
  return ajaxAction(() => indicoAxios.delete(roomURL({room_id: id})), null, () => ({
    type: ROOM_DELETED,
    id,
  }));
}
