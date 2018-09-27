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
import {selectors as configSelectors} from '../config';


const isFetching = ({map}) => map.request === RequestState.STARTED;

export const getMapAspects = ({map}) => map.aspects;

export const isMapEnabled = state => !!configSelectors.getTileServerURL(state);

// the map is visible if it's enabled and we are fetching aspects OR actually have aspects
// that way we don't have a larger room list for a moment while loading aspects, and the
// map has its own loading indicator anyway while there are no aspects
export const isMapVisible = createSelector(
    isMapEnabled,
    isFetching,
    getMapAspects,
    (mapEnabled, aspectsFetching, mapAspects) => mapEnabled && (aspectsFetching || !!mapAspects.length)
);


export const makeGetMapData = (namespace) => ({[namespace]: stateSlice}) => ({
    bounds: stateSlice.map.bounds,
    search: stateSlice.map.search,
    filterBounds: stateSlice.filters.bounds,
});

export const makeIsMapSearchEnabled = (namespace) => ({[namespace]: stateSlice}) => stateSlice.map.search;
