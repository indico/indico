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

/* eslint "react/forbid-component-props": "off" */

import {Card, Col, Icon, List, Row} from 'antd';
import React from 'react';
import propTypes from 'prop-types';

import {PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import textSearchFactory from '../../containers/TextSearch';

import './RoomList.module.scss';


const TextSearch = textSearchFactory('bookRoom');

export default class RoomList extends React.Component {
    componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    render() {
        const {rooms: {list}} = this.props;
        return (
            <div styleName="room-list">
                <TextSearch />
                <div styleName="results-count">
                    <PluralTranslate count={list.length}>
                        <Singular>
                            <Param name="count" value={list.length} /> result found
                        </Singular>
                        <Plural>
                            <Param name="count" value={list.length} /> results found
                        </Plural>
                    </PluralTranslate>
                </div>
                <List grid={{gutter: 12, column: 5}}
                      dataSource={list}
                      renderItem={room => (
                          <List.Item>
                              <Room room={room} />
                          </List.Item>
                      )} />
            </div>
        );
    }
}


RoomList.propTypes = {
    rooms: propTypes.shape({
        list: propTypes.array,
        isFetching: propTypes.bool
    }).isRequired,
    fetchRooms: propTypes.func.isRequired
};


export function Room({room}) {
    const cardDescription = (
        <div styleName="room-card-description">
            {room.full_name}
        </div>
    );

    const cardTitle = (
        <div>
            <Row>
                <Col span={8}>
                    <Icon type="user" /> {room.capacity}
                </Col>
                <Col span={16} styleName="available-equipment">
                    {room.has_webcast_recording && <Icon type="video-camera" />}
                    {room.is_public && <Icon type="unlock" />}
                </Col>
            </Row>
        </div>
    );

    return (
        <Card styleName="room-card"
              cover={<img src={room.small_photo_url} />}>
            <Card.Meta description={cardDescription} title={cardTitle} />
        </Card>
    );
}

Room.propTypes = {
    room: propTypes.object.isRequired
};
