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
import roomsSpriteURL from 'indico-url:rooms_new.sprite';
import {connect} from 'react-redux';
import {Button, Container, Grid, Item, Menu} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import SpriteImage from '../../components/SpriteImage';
import {selectors as roomSelectors} from '../../common/rooms/';
import {selectors as configSelectors} from '../../common/config';

import './AdminArea.module.scss';


class AdminArea extends React.Component {
    static propTypes = {
        locations: PropTypes.object.isRequired,
        roomsSpriteToken: PropTypes.string.isRequired,
    };

    constructor(props) {
        super(props);

        const {locations} = this.props;
        const locationNames = Object.keys(locations);
        this.state = {
            activeItem: locationNames.length ? locationNames[0] : null,
            renderContent: () => {
                return locationNames.length ? this.renderLocationRooms(locationNames[0]) : null;
            }
        };
    }

    renderMenu = () => {
        const {locations} = this.props;
        const {activeItem} = this.state;
        return (
            <Menu size="large" vertical>
                <Menu.Item>
                    <Menu.Header>
                        <Translate>Locations</Translate>
                    </Menu.Header>
                    <Menu.Menu>
                        {Object.keys(locations).map((locationName) => (
                            <Menu.Item key={`location-${locationName}`}
                                       name={locationName}
                                       active={locationName === activeItem}
                                       onClick={() => {
                                           this.setState({
                                               renderContent: () => this.renderLocationRooms(locationName),
                                               activeItem: locationName
                                           });
                                       }}>
                                {locationName}
                            </Menu.Item>
                        ))}
                    </Menu.Menu>
                </Menu.Item>
                <Menu.Item name="manage-locations"
                           active={activeItem === 'manage-locations'}
                           onClick={() => {
                               this.setState({
                                   renderContent: () => 'Manage Locations',
                                   activeItem: 'manage-locations'
                               });
                           }}>
                    <Translate>Manage Locations</Translate>
                </Menu.Item>
                <Menu.Item>
                    <Menu.Header>
                        <Translate>General Settings</Translate>
                    </Menu.Header>
                    <Menu.Menu>
                        <Menu.Item name="equipment-types"
                                   active={activeItem === 'equipment-types'}
                                   onClick={() => {
                                       this.setState({
                                           renderContent: () => 'Equipment types',
                                           activeItem: 'equipment-types'
                                       });
                                   }}>
                            <Translate>Equipment types</Translate>
                        </Menu.Item>
                    </Menu.Menu>
                </Menu.Item>
            </Menu>
        );
    };

    renderLocationRooms = (locationName) => {
        const {locations} = this.props;
        let rooms;

        if (!locationName) {
            rooms = Object.entries(locations)[0][1];
        } else {
            rooms = locations[locationName];
        }

        return (
            <Item.Group divided>
                {rooms.map(this.renderRoomItem)}
            </Item.Group>
        );
    };

    renderRoomItem = (room) => {
        const {roomsSpriteToken} = this.props;
        return (
            <Item key={room.id} styleName="room-item">
                <Item.Image size="small" styleName="room-item-image">
                    <SpriteImage src={roomsSpriteURL({version: roomsSpriteToken})}
                                 pos={room.sprite_position}
                                 origin="0 0"
                                 scale="0.5" />
                </Item.Image>
                <Item.Content>
                    <Item.Header styleName="room-item-header">
                        {room.name}
                        <div>
                            <Button size="mini" icon="pencil" circular />
                            <Button size="mini" icon="trash" negative circular />
                        </div>
                    </Item.Header>
                    <Item.Meta>{room.owner_name}</Item.Meta>
                    <Item.Description>
                        {room.comments}
                    </Item.Description>
                </Item.Content>
            </Item>
        );
    };

    render() {
        const {renderContent} = this.state;
        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        {this.renderMenu()}
                    </Grid.Column>
                    <Grid.Column width={12}>
                        {renderContent()}
                    </Grid.Column>
                </Grid>
            </Container>
        );
    }
}

export default connect(
    (state) => ({
        locations: roomSelectors.getGroupedRoomsByLocation(state),
        roomsSpriteToken: configSelectors.getRoomsSpriteToken(state),
    })
)(AdminArea);
