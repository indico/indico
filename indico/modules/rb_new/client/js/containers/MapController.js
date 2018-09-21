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

import {connect} from 'react-redux';

import MapController from '../components/MapController';
import {
    setFilterParameter,
    toggleMapSearch,
    updateLocation
} from '../actions';


export default function mapControllerFactory(namespace, searchRoomSelectors) {
    const mapStateToProps = (state) => {
        const {
            mapAspects: {list: aspects},
            [namespace]: {map, filters: {bounds}}
        } = state;
        return {
            aspects,
            rooms: searchRoomSelectors.getSearchResultsForMap(state),
            bounds: map.bounds,
            search: map.search,
            filterBounds: bounds
        };
    };

    const mapDispatchToProps = dispatch => ({
        updateLocation: (location, search) => {
            dispatch(updateLocation(namespace, location));
            if (search) {
                dispatch(setFilterParameter(namespace, 'bounds', location));
            }
        },
        toggleMapSearch: (search, location) => {
            dispatch(toggleMapSearch(namespace, search));
            dispatch(setFilterParameter(namespace, 'bounds', search ? location : null));
        },
    });

    return connect(
        mapStateToProps,
        mapDispatchToProps
    )(MapController);
}
