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
import {connect} from 'react-redux';
import {Header, Item, Message} from 'semantic-ui-react';
import {Translate, Param} from 'indico/react/i18n';
import ItemPlaceholder from '../../components/ItemPlaceholder';
import AdminRoomItem from './AdminRoomItem';
import searchBarFactory from '../../components/SearchBar';
import * as adminSelectors from './selectors';


const SearchBar = searchBarFactory('admin', adminSelectors);


function AdminLocationRooms({location, isFetching, filters: {text}}) {
    if (!location || isFetching) {
        return <ItemPlaceholder.Group count={10} />;
    }

    let rooms = location.rooms;
    if (text) {
        rooms = rooms.filter((room) => {
            return room.fullName.toLowerCase().includes(text.trim().toLowerCase());
        });
    }

    return (
        <>
            <Header as="h2">
                <Translate>
                    Location: <Param name="location" value={location.name} />
                </Translate>
            </Header>

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
}

AdminLocationRooms.propTypes = {
    location: PropTypes.object,
    isFetching: PropTypes.bool.isRequired,
    filters: PropTypes.exact({
        text: PropTypes.string,
    }).isRequired,
};

AdminLocationRooms.defaultProps = {
    location: null,
};


export default connect(
    (state, {locationId}) => ({
        isFetching: adminSelectors.isFetchingLocations(state),
        location: adminSelectors.getLocation(state, {locationId}),
        filters: adminSelectors.getFilters(state),
    })
)(AdminLocationRooms);
