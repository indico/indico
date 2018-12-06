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
import {Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import MenuItem from './MenuItem';

import './Menu.module.scss';


const defaultLabels = {
    bookRoom: <Translate>Book a Room</Translate>,
    roomList: <Translate>List of Rooms</Translate>,
    calendar: <Translate>Calendar</Translate>,
    blockings: <Translate>Blockings</Translate>
};


export default function Menu({labels}) {
    const finalLabels = {...defaultLabels, ...labels};
    return (
        <ul styleName="rb-menu">
            <MenuItem key="book" path="/book" namespace="bookRoom">
                <Icon name="add square" />
                {finalLabels.bookRoom}
            </MenuItem>
            <MenuItem key="rooms" path="/rooms" namespace="roomList">
                <Icon name="list" />
                {finalLabels.roomList}
            </MenuItem>
            <MenuItem key="calendar" path="/calendar" namespace="calendar">
                <Icon name="calendar" />
                {finalLabels.calendar}
            </MenuItem>
        </ul>
    );
}

Menu.propTypes = {
    labels: PropTypes.object
};

Menu.defaultProps = {
    labels: {}
};
