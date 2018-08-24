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
import {Item} from 'semantic-ui-react';
import {PluralTranslate} from 'indico/react/i18n';


export default class BlockingCard extends React.Component {
    static propTypes = {
        blocking: PropTypes.object.isRequired
    };

    renderCardHeader() {
        const {blocking} = this.props;
        const {blocked_rooms: blockedRooms} = blocking;

        if (blockedRooms.length === 1) {
            return blockedRooms[0].room.name;
        }

        return PluralTranslate.string('1 room', '{count} rooms', blockedRooms.length, {count: blockedRooms.length});
    }

    render() {
        const {blocking} = this.props;
        const {blocked_rooms: blockedRooms} = blocking;

        return (
            <Item.Group>
                <Item key={blocking.id}>
                    <Item.Image src={blockedRooms[0].room.large_photo_url} size="small" />
                    <Item.Content>
                        <Item.Header>{this.renderCardHeader()}</Item.Header>
                        <Item.Meta>
                            {blocking.start_date} - {blocking.end_date}
                        </Item.Meta>
                        <Item.Description>
                            {blocking.reason}
                        </Item.Description>
                    </Item.Content>
                </Item>
            </Item.Group>
        );
    }
}
