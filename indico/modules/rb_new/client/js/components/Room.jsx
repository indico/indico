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
import {Card, Icon, Image, Label, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {Slot} from 'indico/react/util';
import {TooltipIfTruncated} from 'indico/react/components';
import DimmableImage from  './Dimmer.jsx';


import './Room.module.scss';


export default class Room extends React.Component {
    static propTypes = {
        room: PropTypes.object.isRequired,
        children: PropTypes.node,
        isFavorite: PropTypes.bool
    };

    static defaultProps = {
        isFavorite: false,
        children: null
    };

    shouldComponentUpdate(nextProps) {
        const {isFavorite: nextIsFavorite, room: nextRoom} = nextProps;
        const {room, isFavorite} = this.props;
        const {children} = this.props;
        const {children: nextChildren} = nextProps;

        return nextIsFavorite !== isFavorite || !_.isEqual(room, nextRoom) || !_.isEqual(nextChildren, children);
    }

    renderCardImage = (room, content, actions) => {
        if (actions !== undefined && actions.length !== 0) {
            const dimmerContent = (
                <div>
                    {actions}
                </div>
            );
            return (
                <DimmableImage src={room.large_photo_url}
                               content={content}
                               hoverContent={dimmerContent} />
            );
        } else {
            return (
                <div styleName="room-image">
                    <div styleName="room-extra-info">
                        {content}
                    </div>
                    <Image src={room.large_photo_url} />
                </div>
            );
        }
    };

    render() {
        const {room, children, isFavorite} = this.props;
        const {content, actions} = Slot.split(children);

        return (
            <Card styleName="room-card">
                {isFavorite && <Label corner="right" icon="star" color="yellow" />}
                {this.renderCardImage(room, content, actions)}
                <Card.Content>
                    <TooltipIfTruncated>
                        <Card.Header styleName="room-title">
                            {room.full_name}
                        </Card.Header>
                    </TooltipIfTruncated>
                    <Card.Meta style={{fontSize: '0.8em'}}>
                        {room.division}
                    </Card.Meta>
                    <Card.Description styleName="room-description">
                        {room.comments && (
                            <TooltipIfTruncated>
                                <div styleName="room-comments">
                                    {room.comments}
                                </div>
                            </TooltipIfTruncated>
                        )}
                    </Card.Description>
                </Card.Content>
                <Card.Content styleName="room-content" extra>
                    <>
                        <Icon name="user" /> {room.capacity || Translate.string('Not specified')}
                    </>
                    <span styleName="room-details">
                        {!room.is_reservable && (
                            <Popup trigger={<Icon name="dont" color="grey" />}
                                   content={Translate.string('This room is not bookable')}
                                   position="bottom center"
                                   hideOnScroll />
                        )}
                        {room.has_webcast_recording && <Icon name="video camera" color="green" />}
                        {!room.is_public && (
                            <Popup trigger={<Icon name="lock" color="red" />}
                                   content={Translate.string('This room is not publicly available')}
                                   position="bottom center"
                                   hideOnScroll />
                        )}
                    </span>
                </Card.Content>
            </Card>
        );
    }
}
