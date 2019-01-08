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
import {Button, Card} from 'semantic-ui-react';
import {Slot, Overridable} from 'indico/react/util';
import Room from '../../components/Room';
import {withHoverListener} from '../map/util';

import './RoomRenderer.module.scss';


/**
 * `RoomRenderer` encapsulates the rendering of rooms in both
 * the List of Rooms and the "Book a Room" page.
 */
class RoomRenderer extends React.Component {
    static propTypes = {
        rooms: PropTypes.array.isRequired,
        onSelectRoom: PropTypes.func,
        selectedRooms: PropTypes.object,
        inSelectionMode: PropTypes.bool,
        children: PropTypes.func
    };

    static defaultProps = {
        onSelectRoom: null,
        selectedRooms: {},
        inSelectionMode: false,
        children: null
    };

    RoomComponent = withHoverListener(({room, ...restProps}) => {
        const {onSelectRoom, selectedRooms, inSelectionMode, children} = this.props;

        if (inSelectionMode) {
            const isRoomSelected = room.id in selectedRooms;
            const buttonProps = {compact: true, size: 'tiny'};

            if (!isRoomSelected) {
                buttonProps.icon = 'check';
            } else {
                buttonProps.icon = 'check';
                buttonProps.primary = true;
            }

            return (
                <Room key={room.id} room={room} {...restProps}>
                    <Slot>
                        <Button styleName="selection-add-btn"
                                onClick={() => !!onSelectRoom && onSelectRoom(room)}
                                {...buttonProps} />
                    </Slot>
                </Room>
            );
        } else {
            return (
                <Room key={room.id} room={room} showFavoriteButton {...restProps}>
                    {children ? children(room) : null}
                </Room>
            );
        }
    });

    render() {
        const {rooms, inSelectionMode, selectedRooms} = this.props;
        return (
            <Card.Group stackable>
                {rooms.map(room => (
                    <this.RoomComponent key={room.id}
                                        room={room}
                                        inSelectionMode={inSelectionMode}
                                        selectedRooms={selectedRooms} />
                ))}
            </Card.Group>
        );
    }
}

export default Overridable.component('RoomRenderer', RoomRenderer);
