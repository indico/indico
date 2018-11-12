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
import {Redirect, Route} from 'react-router-dom';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Container, Grid, Item, Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import AdminRoomItem from './AdminRoomItem';
import ItemPlaceholder from '../../components/ItemPlaceholder';
import searchBarFactory from '../../components/SearchBar';
import {selectors as userSelectors} from '../../common/user';
import AdminMenu from './AdminMenu';
import * as adminSelectors from './selectors';
import * as adminActions from './actions';

import './AdminArea.module.scss';


const SearchBar = searchBarFactory('admin', adminSelectors);


class AdminArea extends React.Component {
    static propTypes = {
        locations: PropTypes.array.isRequired,
        isFetchingLocations: PropTypes.bool.isRequired,
        isAdmin: PropTypes.bool.isRequired,
        filters: PropTypes.exact({
            text: PropTypes.string,
        }).isRequired,
        actions: PropTypes.exact({
            fetchLocations: PropTypes.func.isRequired,
        }).isRequired,
    };

    componentDidMount() {
        const {actions: {fetchLocations}} = this.props;
        fetchLocations();
    }

    renderLocationRooms = (locationId) => {
        const {locations, filters: {text}} = this.props;
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

        if (text) {
            rooms = rooms.filter((room) => {
                return room.fullName.toLowerCase().includes(text.toLowerCase());
            });
        }

        return (
            <>
                <SearchBar />
                {rooms.length ? (
                    <>
                        <Item.Group divided>
                            {rooms.map((room) => <AdminRoomItem key={room.id} room={room} />)}
                        </Item.Group>
                    </>
                ) : (
                    <Message info>
                        <Translate>
                            There are no rooms for the specified location.
                        </Translate>
                    </Message>
                )}
            </>
        );
    };

    render() {
        const {isFetchingLocations, isAdmin} = this.props;
        const {locations} = this.props;

        if (!isAdmin) {
            return null;
        }

        const locationURL = (locationId) => `/admin/location/${locationId}`;
        const missingLocationsMessage = (
            <Message info>
                <Translate>
                    There are no locations defined.
                </Translate>
            </Message>
        );

        return (
            <Container styleName="admin-area">
                <Grid columns={2}>
                    <Grid.Column width={4} floated="left">
                        <AdminMenu />
                    </Grid.Column>
                    <Grid.Column width={12}>
                        {isFetchingLocations ? (
                            <ItemPlaceholder.Group count={10} />
                        ) : (
                            <>
                                <Route exact path="/admin"
                                       render={() => {
                                           if (!locations.length) {
                                               return missingLocationsMessage;
                                           }

                                           return (
                                               <Redirect to={locationURL(locations[0].id)} />
                                           );
                                       }} />
                                <Route path="/admin/location/:locationId"
                                       render={({match: {params: {locationId}}}) => {
                                           if (locations.length) {
                                               if (locationId) {
                                                   return this.renderLocationRooms(locationId);
                                               } else {
                                                   return <Redirect to={locationURL(locations[0].id)} />;
                                               }
                                           } else {
                                               return missingLocationsMessage;
                                           }
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
        filters: adminSelectors.getFilters(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchLocations: adminActions.fetchLocations,
        }, dispatch),
    })
)(AdminArea);
