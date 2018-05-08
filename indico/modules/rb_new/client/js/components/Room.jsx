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
import {Card, Dimmer, Icon, Image, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {Slot} from 'indico/react/util';
import {TooltipIfTruncated} from 'indico/react/components';


import './Room.module.scss';


export default class Room extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            dimmed: false
        };
    }

    toggleDimmer = (state) => {
        this.setState({dimmed: state});
    }

    renderDimmedImage = (dimmer, content) => {
        const {dimmed} = this.state;
        const newProps = Object.assign({}, dimmer);
        delete newProps['className'];

        return (
            <div styleName="room-image">
                {!dimmed && content && (
                    <div styleName="room-extra-info">
                        {content}
                    </div>
                )}
                <Image {...dimmer} />
            </div>
        );
    }

    renderCardImage = (room, content, actions) => {
        const {dimmed} = this.state;

        if (actions !== undefined && actions.length !== 0) {
            const dimmerContent = (
                <div>
                    {actions}
                </div>
            );

            return (
                <Dimmer.Dimmable as={(dimmer) => this.renderDimmedImage(dimmer, content)}
                                 dimmed={dimmed}
                                 dimmer={{active: dimmed, content: dimmerContent}}
                                 src={room.large_photo_url}
                                 onMouseEnter={() => this.toggleDimmer(true)}
                                 onMouseLeave={() => this.toggleDimmer(false)}
                                 blurring />
            );
        } else {
            return (
                <div styleName="room-image">
                    <div styleName="room-extra-info">
                        {!dimmed && content}
                    </div>
                    <Image src={room.large_photo_url} />
                </div>
            );
        }
    }

    render() {
        const {room, children} = this.props;
        const {content, actions} = Slot.split(children);

        return (
            <Card styleName="room-card">
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

Room.propTypes = {
    room: PropTypes.object.isRequired,
    children: PropTypes.node.isRequired
};
