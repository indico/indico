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
import {toClasses} from 'indico/react/util';
import roomListStyles from './RoomList.module.scss';


export default class RoomList extends React.Component {
    componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    render() {
        const {rooms} = this.props;
        return (
            <div className={toClasses(roomListStyles['room-list'])}>
                <div className={toClasses(roomListStyles['results-count'])}>
                    <PluralTranslate>
                        <Singular>
                            <Param name="count" value={rooms.length} /> result found
                        </Singular>
                        <Plural>
                            <Param name="count" value={rooms.length} /> results found
                        </Plural>
                    </PluralTranslate>
                </div>
                <List grid={{gutter: 12, column: 5}}
                      dataSource={rooms}
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
    rooms: propTypes.array.isRequired,
    fetchRooms: propTypes.func.isRequired
};


export function Room({room}) {
    const cardDescription = (
        <div className={toClasses(roomListStyles['room-card-description'])}>
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
        <Card className={toClasses(roomListStyles['room-card'])}
              cover={<img src={room.small_photo_url} width="120px" height="170px" />}>
            <Card.Meta description={cardDescription} title={cardTitle} />
        </Card>
    );
}

Room.propTypes = {
    room: propTypes.object.isRequired
};
