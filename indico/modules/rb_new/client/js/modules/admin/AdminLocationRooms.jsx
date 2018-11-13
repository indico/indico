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
import {Item, Message} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import ItemPlaceholder from '../../components/ItemPlaceholder';
import AdminRoomItem from './AdminRoomItem';
import searchBarFactory from '../../components/SearchBar';
import * as adminSelectors from './selectors';


const SearchBar = searchBarFactory('admin', adminSelectors);


function AdminLocationRooms({locations, isFetchingLocations, locationId, filters: {text}}) {
    if (isFetchingLocations) {
        return <ItemPlaceholder.Group count={10} />;
    } else if (!locations.length) {
        return (
            <Message info>
                <Translate>
                    There are no locations defined.
                </Translate>
            </Message>
        );
    }

    let rooms = [];
    if (locations.length) {
        const location = locations.find((loc) => loc.id === locationId);
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
}

AdminLocationRooms.propTypes = {
    locations: PropTypes.array.isRequired,
    locationId: PropTypes.number.isRequired,
    filters: PropTypes.exact({
        text: PropTypes.string,
    }).isRequired,
};


export default connect(
    (state) => ({
        isFetchingLocations: adminSelectors.isFetchingLocations(state),
        locations: adminSelectors.getAllLocations(state),
        filters: adminSelectors.getFilters(state),
    })
)(AdminLocationRooms);
