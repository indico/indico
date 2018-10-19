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

import React from 'react';
import PropTypes from 'prop-types';
import {Dropdown, Icon} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {push as pushRoute} from 'connected-react-router';
import {Translate} from 'indico/react/i18n';

import {selectors as userSelectors} from '../common/user';
import {actions as blockingsActions} from '../modules/blockings';
import {actions as filtersActions} from '../common/filters';


function UserActions({isAdmin, hasOwnedRooms, gotoMyRoomsList, gotoMyBlockings}) {
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
        onClick: gotoMyBlockings,
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
    isAdmin: PropTypes.bool.isRequired,
    hasOwnedRooms: PropTypes.bool.isRequired,
    gotoMyRoomsList: PropTypes.func.isRequired,
    gotoMyBlockings: PropTypes.func.isRequired,
};


export default connect(
    state => ({
        isAdmin: userSelectors.isUserAdmin(state),
        hasOwnedRooms: userSelectors.hasOwnedRooms(state),
    }),
    dispatch => ({
        gotoMyRoomsList() {
            dispatch(filtersActions.setFilterParameter('roomList', 'onlyMine', true));
            dispatch(pushRoute('/rooms?mine=true'));
        },
        gotoMyBlockings() {
            dispatch(blockingsActions.setFilterParameter('myBlockings', true));
            dispatch(pushRoute('/blockings?myBlockings=true'));
        },
    })
)(UserActions);
