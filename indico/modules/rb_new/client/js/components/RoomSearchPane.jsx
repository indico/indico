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
import {Card, Icon, Image} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';

import {Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';

import './RoomSearchPane.module.scss';


export default class RoomSearchPane extends React.Component {
    static propTypes = {
        rooms: PropTypes.shape({
            list: PropTypes.array,
            total: PropTypes.number,
            isFetching: PropTypes.bool
        }).isRequired,
        fetchRooms: PropTypes.func.isRequired,
        filterBar: PropTypes.element.isRequired,
        searchBar: PropTypes.element.isRequired
    };

    componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    loadMore = () => {
        const {fetchRooms} = this.props;
        fetchRooms(false);
    };

    render() {
        const {rooms: {list, total, isFetching}, filterBar, searchBar} = this.props;

        return (
            <div className="ui" styleName="room-list">
                {filterBar}
                {searchBar}
                <div styleName="results-count">
                    <PluralTranslate count={total}>
                        <Singular>
                            <Param name="count" value={total} /> result found
                        </Singular>
                        <Plural>
                            <Param name="count" value={total} /> results found
                        </Plural>
                    </PluralTranslate>
                </div>
                <LazyScroll hasMore={total > list.length} loadMore={this.loadMore} isFetching={isFetching}>
                    <Card.Group stackable>
                        {list.map((room) => (
                            <Room key={room.id} room={room} />
                        ))}
                    </Card.Group>
                </LazyScroll>
            </div>
        );
    }
}

export function Room({room}) {
    return (
        <Card styleName="room-card">
            <Image src={room.large_photo_url} />
            <Card.Content>
                <Card.Description styleName="room-description">
                    {room.full_name}
                </Card.Description>
            </Card.Content>
            <Card.Content styleName="room-content" extra>
                <Icon name="user" /> {room.capacity}
                <span styleName="room-details">
                    {room.has_webcast_recording && <Icon name="video camera" />}
                    {!room.is_public && <Icon name="lock" />}
                </span>
            </Card.Content>
        </Card>
    );
}

Room.propTypes = {
    room: PropTypes.object.isRequired
};
