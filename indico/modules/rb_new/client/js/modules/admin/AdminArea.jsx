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

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Container, Grid, Icon, Item, Menu, Placeholder} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import AdminRoomItem from './AdminRoomItem';
import * as adminSelectors from './selectors';
import * as adminActions from './actions';

import './AdminArea.module.scss';


class AdminArea extends React.Component {
    static propTypes = {
        locations: PropTypes.array.isRequired,
        isFetchingLocations: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {
        activeItem: null,
        locations: [],
    };

    static getDerivedStateFromProps(props, prevState) {
        const {locations} = props;
        if (locations.length && !prevState.activeItem) {
            return {
                activeItem: `location-${locations[0].name}`,
            };
        }

        return {...prevState};
    }

    componentDidMount() {
        const {actions: {fetchLocations}} = this.props;
        fetchLocations();
    }

    renderMenu = () => {
        const {locations} = this.props;
        const {activeItem} = this.state;
        const hasLocations = locations.length !== 0;

        return (
            <Menu size="large" styleName="admin-menu" vertical>
                <Menu.Item>
                    <Menu.Header styleName="locations-header">
                        <Translate>Locations</Translate>
                        <Icon name="setting" />
                    </Menu.Header>
                    {!hasLocations && (
                        <p>
                            <Translate>There are no Locations. Click 'Manage Locations' to add one.</Translate>
                        </p>
                    )}
                    {hasLocations && (
                        <Menu.Menu>
                            {locations.map((location) => (
                                <Menu.Item key={`location-${location.name}`}
                                           active={activeItem === `location-${location.name}`}
                                           name={location.name}
                                           onClick={() => {
                                               this.setState({
                                                   renderContent: () => this.renderLocationRooms(location.name),
                                                   activeItem: `location-${location.name}`
                                               });
                                           }}>
                                    {location.name}
                                </Menu.Item>
                            ))}
                        </Menu.Menu>
                    )}
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

    renderItemPlaceholders = () => {
        return (
            <Item.Group>
                {_.range(0, 10).map((i) => (
                    <Item key={i}>
                        <Item.Image>
                            <Placeholder>
                                <Placeholder.Image />
                            </Placeholder>
                        </Item.Image>
                        <Item.Content>
                            <Placeholder>
                                <Placeholder.Line length="very short" />
                            </Placeholder>
                            <Item.Meta>
                                <Placeholder>
                                    <Placeholder.Line length="short" />
                                </Placeholder>
                            </Item.Meta>
                            <Item.Description>
                                <Placeholder>
                                    <Placeholder.Line length="full" />
                                    <Placeholder.Line length="full" />
                                </Placeholder>
                            </Item.Description>
                        </Item.Content>
                    </Item>
                ))}
            </Item.Group>
        );
    };

    renderLocationRooms = (locationName) => {
        const {locations} = this.props;
        let rooms;

        if (!locations.length) {
            rooms = [];
        } else if (!locationName) {
            rooms = locations[0].rooms;
        } else {
            rooms = locations.find((location) => location.name === locationName).rooms; // TODO: change to id
        }

        rooms = rooms.sort((a, b) => a.fullName.localeCompare(b.fullName));
        return (
            <Item.Group divided>
                {rooms.map((room) => <AdminRoomItem key={room.id} room={room} />)}
            </Item.Group>
        );
    };

    render() {
        const {renderContent} = this.state;
        const {isFetchingLocations} = this.props;
        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        {this.renderMenu()}
                    </Grid.Column>
                    <Grid.Column width={12}>
                        {isFetchingLocations ? (
                            this.renderItemPlaceholders()
                        ) : (
                            renderContent ? renderContent() : this.renderLocationRooms()
                        )}
                    </Grid.Column>
                </Grid>
            </Container>
        );
    }
}

export default connect(
    state => ({
        locations: adminSelectors.getAllLocations(state),
        isFetchingLocations: adminSelectors.isFetchingLocations(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
        }, dispatch),
    })
)(AdminArea);
