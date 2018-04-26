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

import RoomList from '../components/pages/RoomList';
import {fetchMapDefaultAspects, fetchRooms, updateLocation} from '../actions';


const mapStateToProps = ({roomList}) => ({...roomList});

const mapDispatchToProps = dispatch => ({
    fetchMapDefaultAspects: (callback) => {
        dispatch(fetchMapDefaultAspects()).then(callback);
    },
    updateLocation: (location) => {
        dispatch(updateLocation(location));
    },
    fetchRooms: (clear = true) => {
        dispatch(fetchRooms('roomList', clear));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(RoomList);
