// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fetchEquipmentTypesURL from 'indico-url:rb.equipment_types';
import fetchRoomURL from 'indico-url:rb.room';
import fetchRoomAttributesURL from 'indico-url:rb.room_attributes';
import fetchRoomAvailabilityURL from 'indico-url:rb.room_availability';
import fetchRoomsURL from 'indico-url:rb.rooms';

import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {ajaxAction} from 'indico/utils/redux';

import {openModal} from '../../actions';

export const FETCH_EQUIPMENT_TYPES_REQUEST = 'rooms/FETCH_EQUIPMENT_TYPES_REQUEST';
export const FETCH_EQUIPMENT_TYPES_SUCCESS = 'rooms/FETCH_EQUIPMENT_TYPES_SUCCESS';
export const FETCH_EQUIPMENT_TYPES_ERROR = 'rooms/FETCH_EQUIPMENT_TYPES_ERROR';
export const EQUIPMENT_TYPES_RECEIVED = 'rooms/EQUIPMENT_TYPES_RECEIVED';

export const ROOM_DETAILS_RECEIVED = 'rooms/ROOM_DETAILS_RECEIVED';
export const FETCH_ROOM_DETAILS_REQUEST = 'rooms/FETCH_ROOM_DETAILS_REQUEST';
export const FETCH_ROOM_DETAILS_SUCCESS = 'rooms/FETCH_ROOM_DETAILS_SUCCESS';
export const FETCH_ROOM_DETAILS_ERROR = 'rooms/FETCH_ROOM_DETAILS_ERROR';

export const ROOMS_RECEIVED = 'rooms/ROOMS_RECEIVED';
export const FETCH_ROOMS_REQUEST = 'rooms/FETCH_ROOMS_REQUEST';
export const FETCH_ROOMS_SUCCESS = 'rooms/FETCH_ROOMS_SUCCESS';
export const FETCH_ROOMS_ERROR = 'rooms/FETCH_ROOMS_ERROR';

export const AVAILABILITY_RECEIVED = 'rooms/AVAILABILITY_RECEIVED';
export const FETCH_AVAILABILITY_REQUEST = 'rooms/FETCH_AVAILABILITY_REQUEST';
export const FETCH_AVAILABILITY_SUCCESS = 'rooms/FETCH_AVAILABILITY_SUCCESS';
export const FETCH_AVAILABILITY_ERROR = 'rooms/FETCH_AVAILABILITY_ERROR';

export const ATTRIBUTES_RECEIVED = 'rooms/ATTRIBUTES_RECEIVED';
export const FETCH_ATTRIBUTES_REQUEST = 'rooms/FETCH_ATTRIBUTES_REQUEST';
export const FETCH_ATTRIBUTES_SUCCESS = 'rooms/FETCH_ATTRIBUTES_SUCCESS';
export const FETCH_ATTRIBUTES_ERROR = 'rooms/FETCH_ATTRIBUTES_ERROR';

export function fetchEquipmentTypes() {
  return ajaxAction(
    () => indicoAxios.get(fetchEquipmentTypesURL()),
    FETCH_EQUIPMENT_TYPES_REQUEST,
    [EQUIPMENT_TYPES_RECEIVED, FETCH_EQUIPMENT_TYPES_SUCCESS],
    FETCH_EQUIPMENT_TYPES_ERROR
  );
}

export function fetchRoom(id) {
  return ajaxAction(
    () => indicoAxios.get(fetchRoomURL({room_id: id})),
    FETCH_ROOM_DETAILS_REQUEST,
    [ROOM_DETAILS_RECEIVED, FETCH_ROOM_DETAILS_SUCCESS],
    FETCH_ROOM_DETAILS_ERROR
  );
}

export function fetchRooms() {
  return ajaxAction(
    () => indicoAxios.get(fetchRoomsURL()),
    FETCH_ROOMS_REQUEST,
    [ROOMS_RECEIVED, FETCH_ROOMS_SUCCESS],
    FETCH_ROOMS_ERROR
  );
}

export function fetchDetails(id, force = false) {
  return async dispatch => {
    dispatch(fetchAvailability(id, force));
    dispatch(fetchAttributes(id, force));
  };
}

export function fetchAvailability(id, force = false) {
  return async (dispatch, getStore) => {
    const {
      rooms: {availability: rooms},
    } = getStore();
    if (!force && id in rooms) {
      return;
    }
    return await ajaxAction(
      () => indicoAxios.get(fetchRoomAvailabilityURL({room_id: id})),
      FETCH_AVAILABILITY_REQUEST,
      [AVAILABILITY_RECEIVED, FETCH_AVAILABILITY_SUCCESS],
      FETCH_AVAILABILITY_ERROR,
      data => ({id, availability: camelizeKeys(data)})
    )(dispatch);
  };
}

export function fetchAttributes(id, force = false) {
  return async (dispatch, getStore) => {
    const {
      rooms: {attributes: rooms},
    } = getStore();
    if (!force && id in rooms) {
      return;
    }
    return await ajaxAction(
      () => indicoAxios.get(fetchRoomAttributesURL({room_id: id})),
      FETCH_ATTRIBUTES_REQUEST,
      [ATTRIBUTES_RECEIVED, FETCH_ATTRIBUTES_SUCCESS],
      FETCH_ATTRIBUTES_ERROR,
      data => ({id, attributes: data})
    )(dispatch);
  };
}

export const openRoomDetails = roomId => openModal('room-details', roomId);
export const openRoomDetailsBook = roomId => openModal('room-details-book', roomId);
