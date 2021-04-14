// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

import {selectors as configSelectors} from '../config';

const isFetching = ({map}) => map.request === RequestState.STARTED;

export const getMapAreas = ({map}) => map.areas;

export const isMapEnabled = state => !!configSelectors.getTileServerURL(state);

// the map is visible if it's enabled and we are fetching areas OR actually have areas
// that way we don't have a larger room list for a moment while loading areas, and the
// map has its own loading indicator anyway while there are no areas
export const isMapVisible = createSelector(
  isMapEnabled,
  isFetching,
  getMapAreas,
  (mapEnabled, areasFetching, mapAreas) => mapEnabled && (areasFetching || !!mapAreas.length)
);

export const makeGetMapData = namespace => ({[namespace]: stateSlice}) => ({
  bounds: stateSlice.map.bounds,
  search: stateSlice.map.search,
  filterBounds: stateSlice.filters.bounds,
});

export const makeIsMapSearchEnabled = namespace => ({[namespace]: stateSlice}) =>
  stateSlice.map.search;

export const getHoveredRoom = ({map}) => map.ui.hoveredRoom;
