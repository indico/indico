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

import propTypes from 'prop-types';
import React from 'react';
import {Map, TileLayer} from 'react-leaflet';

import 'leaflet/dist/leaflet.css';
import './RoomBookingMap.module.scss';

export default function RoomBookingMap({center, zoom}) {
    return (
        <div styleName="map-container">
            <Map center={center} zoom={zoom}>
                <TileLayer attribution='© <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
                           url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            </Map>
        </div>
    );
}

RoomBookingMap.propTypes = {
    center: propTypes.array.isRequired,
    zoom: propTypes.number.isRequired
};
