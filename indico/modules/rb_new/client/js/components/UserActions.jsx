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

/* eslint "react/forbid-component-props": "off" */

import React from 'react';
import propTypes from 'prop-types';
import {Dropdown, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';


export default function UserActions({isAdmin, hasOwnedRooms, gotoMyRoomsList}) {
    const avatar = <Icon name="user" size="large" />;
    const options = [];
    options.push({
        key: 'my_bookings',
        text: Translate.string('My Bookings'),
        disabled: true,
    });
    if (hasOwnedRooms) {
        options.push({
            key: 'bookings_my_rooms',
            text: Translate.string('Bookings in My Rooms'),
            disabled: true,
        });
        options.push({
            key: 'my_rooms',
            text: Translate.string('List of My Rooms'),
            onClick: gotoMyRoomsList,
        });
    }
    options.push({
        key: 'my_blockings',
        text: Translate.string('My Blockings'),
        disabled: true,
    });
    if (isAdmin) {
        options.push({
            key: 'isAdmin',
            text: Translate.string('Administration'),
            disabled: true,
        });
    }
    return (
        <Dropdown trigger={avatar} options={options} pointing="top right" />
    );
}

UserActions.propTypes = {
    isAdmin: propTypes.bool.isRequired,
    hasOwnedRooms: propTypes.bool.isRequired,
    gotoMyRoomsList: propTypes.func.isRequired,
};
