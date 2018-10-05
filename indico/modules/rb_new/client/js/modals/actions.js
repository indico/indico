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

import {push} from 'connected-react-router';

import {history} from '../store';


function openModal(name, value = null, payload = null) {
    const {location: {pathname: path, search: queryString}} = history;
    let data = name;
    if (value !== null) {
        data += `:${value}`;
        if (payload !== null) {
            data += `:${JSON.stringify(payload)}`;
        }
    }
    // eslint-disable-next-line prefer-template
    return push(path + (queryString ? `${queryString}&` : '?') + `modal=${encodeURIComponent(data)}`);
}

export const openRoomDetails = (roomId) => openModal('room-details', roomId);
export const openRoomDetailsBook = (roomId) => openModal('room-details-book', roomId);
export const openBookRoom = (roomId, data = null) => openModal('book-room', roomId, data);
export const openUnavailableRooms = () => openModal('unavailable-rooms');
export const openBookingForm = (roomId, data) => openModal('booking-form', roomId, data);
export const openBlockingDetails = (blockingId) => openModal('blocking-details', blockingId);
