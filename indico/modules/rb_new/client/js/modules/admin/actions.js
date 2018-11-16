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

import fetchLocationsURL from 'indico-url:rooms_new.admin_locations';
import equipmentTypesURL from 'indico-url:rooms_new.admin_equipment_types';
import featuresURL from 'indico-url:rooms_new.admin_features';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {ajaxAction, submitFormAction} from 'indico/utils/redux';
import {actions as filtersActions} from '../../common/filters';


export const FETCH_LOCATIONS_REQUEST = 'admin/FETCH_LOCATIONS_REQUEST';
export const FETCH_LOCATIONS_SUCCESS = 'admin/FETCH_LOCATIONS_SUCCESS';
export const FETCH_LOCATIONS_ERROR = 'admin/FETCH_LOCATIONS_ERROR';
export const LOCATIONS_RECEIVED = 'admin/LOCATIONS_RECEIVED';

export const FETCH_FEATURES_REQUEST = 'admin/FETCH_FEATURES_REQUEST';
export const FETCH_FEATURES_SUCCESS = 'admin/FETCH_FEATURES_SUCCESS';
export const FETCH_FEATURES_ERROR = 'admin/FETCH_FEATURES_ERROR';
export const FEATURES_RECEIVED = 'admin/FEATURES_RECEIVED';

export const FETCH_EQUIPMENT_TYPES_REQUEST = 'admin/FETCH_EQUIPMENT_TYPES_REQUEST';
export const FETCH_EQUIPMENT_TYPES_SUCCESS = 'admin/FETCH_EQUIPMENT_TYPES_SUCCESS';
export const FETCH_EQUIPMENT_TYPES_ERROR = 'admin/FETCH_EQUIPMENT_TYPES_ERROR';
export const EQUIPMENT_TYPES_RECEIVED = 'admin/EQUIPMENT_TYPES_RECEIVED';
export const EQUIPMENT_TYPE_RECEIVED = 'admin/EQUIPMENT_TYPE_RECEIVED';
export const EQUIPMENT_TYPE_DELETED = 'admin/EQUIPMENT_TYPE_DELETED';

export const FILTER_NAMESPACE = 'admin';


export function fetchLocations() {
    return ajaxAction(
        () => indicoAxios.get(fetchLocationsURL()),
        FETCH_LOCATIONS_REQUEST,
        [LOCATIONS_RECEIVED, FETCH_LOCATIONS_SUCCESS],
        FETCH_LOCATIONS_ERROR
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

export function clearTextFilter() {
    return filtersActions.setFilterParameter(FILTER_NAMESPACE, 'text', null);
}

export function deleteEquipmentType(id) {
    return async (dispatch) => {
        try {
            await indicoAxios.delete(equipmentTypesURL({equipment_type_id: id}));
        } catch (error) {
            handleAxiosError(error, true);
            return;
        }
        dispatch({type: EQUIPMENT_TYPE_DELETED, id});
    };
}

export function updateEquipmentType(id, data) {
    return submitFormAction(
        () => indicoAxios.patch(equipmentTypesURL({equipment_type_id: id}), data),
        null, EQUIPMENT_TYPE_RECEIVED
    );
}

export function createEquipmentType(data) {
    return submitFormAction(
        () => indicoAxios.post(equipmentTypesURL(), data),
        null, EQUIPMENT_TYPE_RECEIVED
    );
}
