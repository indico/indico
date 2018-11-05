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
import {Link, Redirect, Route} from 'react-router-dom';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Container, Grid, Icon, Item, Menu, Message, Placeholder} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import AdminRoomItem from './AdminRoomItem';
import ItemPlaceholder from '../../components/ItemPlaceholder';
import {selectors as userSelectors} from '../../common/user';
import * as adminSelectors from './selectors';
import * as adminActions from './actions';

import './AdminArea.module.scss';


class AdminArea extends React.Component {
    static propTypes = {
        locations: PropTypes.array.isRequired,
        isFetchingLocations: PropTypes.bool.isRequired,
        isAdmin: PropTypes.bool.isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchLocations}} = this.props;
        fetchLocations();
    }

    renderMenuPlaceholder = () => {
        return (
            <Menu vertical>
                <Menu.Item>
                    <Menu.Header>
                        <Placeholder>
                            <Placeholder.Line length="medium" />
                        </Placeholder>
                    </Menu.Header>
                    <Menu.Menu>
                        <Menu.Item>
                            <Placeholder>
                                <Placeholder.Line length="short" />
                                <Placeholder.Line length="short" />
                                <Placeholder.Line length="short" />
                                <Placeholder.Line length="short" />
                            </Placeholder>
                        </Menu.Item>
                    </Menu.Menu>
                </Menu.Item>
            </Menu>
        );
    };

    renderMenu = () => {
        const {locations} = this.props;
        const hasLocations = locations.length !== 0;

        return (
            <Menu size="large" styleName="admin-menu" vertical>
                <Menu.Item>
                    <Menu.Header styleName="locations-header">
                        <Translate>Locations</Translate>
                        <Icon name="setting" />
                    </Menu.Header>
                    {hasLocations && (
                        <Menu.Menu>
                            {locations.map((location) => (
                                <Route path={`/admin/location/${location.id}`} key={`location-${location.id}`}>
                                    {({match}) => (
                                        <Link to={`/admin/location/${location.id}`}>
                                            <Menu.Item active={!!match}>
                                                {location.name}
                                            </Menu.Item>
                                        </Link>
                                    )}
                                </Route>
                            ))}
                        </Menu.Menu>
                    )}
                </Menu.Item>
                <Menu.Item>
                    <Menu.Header>
                        <Translate>General Settings</Translate>
                    </Menu.Header>
                    <Menu.Menu>
                        <Route path="/admin/equipment-types">
                            {({match}) => (
                                <Link to="/admin/equipment-types">
                                    <Menu.Item active={!!match}>
                                        <Translate>Equipment types</Translate>
                                    </Menu.Item>
                                </Link>
                            )}
                        </Route>
                    </Menu.Menu>
                </Menu.Item>
            </Menu>
        );
    };

    renderLocationRooms = (locationId) => {
        const {locations} = this.props;
        let rooms;

        if (!locations.length) {
            rooms = [];
        } else {
            const location = locations.find((loc) => loc.id === parseInt(locationId, 10));
            if (!location) {
                rooms = [];
            } else {
                rooms = location.rooms;
            }
        }

        return (
            <Item.Group divided>
                {rooms.map((room) => <AdminRoomItem key={room.id} room={room} />)}
            </Item.Group>
        );
    };

    render() {
        const {isFetchingLocations, isAdmin} = this.props;
        const {locations} = this.props;

        if (!isAdmin) {
            return null;
        }

        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        {isFetchingLocations ? this.renderMenuPlaceholder() : this.renderMenu()}
                    </Grid.Column>
                    <Grid.Column width={12}>
                        {isFetchingLocations ? (
                            <ItemPlaceholder.Group count={10} />
                        ) : (
                            <>
                                <Route exact path="/admin" render={() => {
                                    if (!locations.length) {
                                        return (
                                            <Message>
                                                <Translate>
                                                    No room locations have been defined.
                                                </Translate>
                                            </Message>
                                        );
                                    }

                                    return <Redirect to={`/admin/location/${locations[0].id}`} />;
                                }} />
                                <Route exact path="/admin/location/:locationId"
                                       render={({match: {params: {locationId}}}) => {
                                           return this.renderLocationRooms(locationId);
                                       }} />
                                <Route exact path="/admin/equipment-types"
                                       render={() => (
                                           <div>
                                               <Translate>
                                                   Equipment Types
                                               </Translate>
                                           </div>
                                       )} />
                            </>
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
        isAdmin: userSelectors.isUserAdmin(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
        }, dispatch),
    })
)(AdminArea);
