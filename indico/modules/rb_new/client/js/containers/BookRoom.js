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

import BookRoom from '../components/pages/BookRoom';
import {fetchMapDefaultAspects, fetchRooms, setFilterParameter, toggleMapSearch, updateLocation} from '../actions';


const mapStateToProps = ({bookRoom}) => ({...bookRoom});

const mapDispatchToProps = dispatch => ({
    fetchMapDefaultAspects: (callback) => {
        dispatch(fetchMapDefaultAspects()).then(callback);
    },
    updateLocation: (location, search) => {
        dispatch(updateLocation(location));
        if (search) {
            dispatch(setFilterParameter('bookRoom', 'bounds', location));
        }
    },
    toggleMapSearch: (search, location) => {
        dispatch(toggleMapSearch(search));
        dispatch(setFilterParameter('bookRoom', 'bounds', search ? location : {}));
    },
    fetchRooms: (clear = true) => {
        dispatch(fetchRooms('bookRoom', clear));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(BookRoom);
