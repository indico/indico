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
import {Menu, Icon} from 'antd';
import propTypes from 'prop-types';

import {Slot, toClasses} from 'indico/react/util';
import ArrowDownMenu, {styles as arrowDownStyles} from 'indico/react/components/ArrowDownMenu';

import userActionsStyles from './UserActions.module.scss';


export default function UserActions({hasRooms, hasBlockings, isAdmin}) {
    return (
        <ArrowDownMenu>
            <Slot name="avatar">
                <Icon className={toClasses(userActionsStyles['user-icon'], arrowDownStyles['icon-change-hover'])}
                      type="user" size="large" />
            </Slot>
            <Slot>
                <Menu>
                    <Menu.Item>My Bookings</Menu.Item>
                    {hasRooms && <Menu.Item>Bookings in My Rooms</Menu.Item>}
                    {hasRooms && <Menu.Item>List of My Rooms</Menu.Item>}
                    {hasBlockings && <Menu.Item>My Blockings</Menu.Item>}
                    {isAdmin && <Menu.Item>Administration</Menu.Item>}
                </Menu>
            </Slot>
        </ArrowDownMenu>
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
