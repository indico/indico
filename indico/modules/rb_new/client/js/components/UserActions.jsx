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
import ReactDOM from 'react-dom';
import {Menu, Dropdown, Icon} from 'antd';
import propTypes from 'prop-types';

import './UserActions.module.scss';


function UserActions({hasRooms, hasBlockings, isAdmin}) {
    const menu = (
        <Menu>
            <Menu.Item>My Bookings</Menu.Item>
            {hasRooms && <Menu.Item>Bookings in My Rooms</Menu.Item>}
            {hasRooms && <Menu.Item>List of My Rooms</Menu.Item>}
            {hasBlockings && <Menu.Item>My Blockings</Menu.Item>}
            {isAdmin && <Menu.Item>Administration</Menu.Item>}
        </Menu>
    );
    return (
        <Dropdown overlay={menu}>
            <span styleName="container">
                <Icon styleName="anticon" type="user" size="large" />
                <Icon styleName="anticon" type="down" />
            </span>
        </Dropdown>
    );
}

UserActions.propTypes = {
    hasRooms: propTypes.bool,
    hasBlockings: propTypes.bool,
    isAdmin: propTypes.bool
};

UserActions.defaultProps = {
    hasRooms: false,
    hasBlockings: false,
    isAdmin: false
};

export default function setupUserActions(element, userData) {
    ReactDOM.render(
        <UserActions {...userData} />,
        element
    );
}
