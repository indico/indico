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
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Card, Icon, Label, Popup, Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {Slot} from 'indico/react/util';
import {TooltipIfTruncated} from 'indico/react/components';
import SpriteImage from './SpriteImage';
import DimmableImage from './DimmableImage';
import {actions as userActions, selectors as userSelectors} from '../common/user';
import RoomFeatureEntry from './RoomFeatureEntry';

import './Room.module.scss';


class Room extends React.Component {
    static propTypes = {
        room: PropTypes.object.isRequired,
        children: PropTypes.node,
        showFavoriteButton: PropTypes.bool,
        isFavorite: PropTypes.bool.isRequired,
        addFavoriteRoom: PropTypes.func.isRequired,
        delFavoriteRoom: PropTypes.func.isRequired
    };

    static defaultProps = {
        showFavoriteButton: false,
        children: null
    };

    shouldComponentUpdate(nextProps) {
        const {isFavorite: nextIsFavorite, room: nextRoom} = nextProps;
        const {room, isFavorite} = this.props;
        const {children} = this.props;
        const {children: nextChildren} = nextProps;

        return (
            !_.isEqual(room, nextRoom) ||
            nextIsFavorite !== isFavorite ||
            !_.isEqual(nextChildren, children)
        );
    }

    renderFavoriteButton() {
        const {addFavoriteRoom, delFavoriteRoom, room, isFavorite} = this.props;
        const button = (
            <Button icon="star" color={isFavorite ? 'yellow' : 'teal'} circular
                    onClick={() => (isFavorite ? delFavoriteRoom : addFavoriteRoom)(room.id)} />
        );
        const tooltip = isFavorite
            ? Translate.string('Remove from favourites')
            : Translate.string('Add to favourites');
        return <Popup trigger={button} content={tooltip} position="top center" />;
    }

    renderCardImage = (room, content, actions) => {
        const {showFavoriteButton} = this.props;
        const sprite = <SpriteImage pos={room.spritePosition} />;

        if ((actions !== undefined && actions.length !== 0) || showFavoriteButton) {
            const dimmerContent = (
                <div>
                    {actions}
                    {showFavoriteButton && this.renderFavoriteButton()}
                </div>
            );
            return (
                <DimmableImage content={content}
                               hoverContent={dimmerContent}>
                    {sprite}
                </DimmableImage>
            );
        } else {
            return (
                <div styleName="room-image">
                    <div styleName="room-extra-info">
                        {content}
                    </div>
                    {sprite}
                </div>
            );
        }
    };

    render() {
        const {
            room, children, isFavorite, showFavoriteButton, addFavoriteRoom, delFavoriteRoom,
            ...restProps
        } = this.props;
        const {content, actions} = Slot.split(children);

        return (
            <Card styleName="room-card" {...restProps}>
                {isFavorite && <Label corner="right" icon="star" color="yellow" />}
                {this.renderCardImage(room, content, actions)}
                <Card.Content>
                    <TooltipIfTruncated>
                        <Card.Header styleName="room-title">
                            {room.fullName}
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
                        {room.features.map(feature => (
                            <RoomFeatureEntry key={feature.name} feature={feature} color="green" />
                        ))}
                        {!room.isReservable && (
                            <Popup trigger={<Icon name="dont" color="grey" />}
                                   content={Translate.string('This room is not bookable')}
                                   position="bottom center"
                                   hideOnScroll />
                        )}
                        {!room.isPublic && (
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

export default connect(
    () => {
        const isFavoriteRoom = userSelectors.makeIsFavoriteRoom();
        return (state, props) => ({
            isFavorite: isFavoriteRoom(state, props)
        });
    },
    dispatch => bindActionCreators({
        addFavoriteRoom: userActions.addFavoriteRoom,
        delFavoriteRoom: userActions.delFavoriteRoom,
    }, dispatch)
)(Room);
