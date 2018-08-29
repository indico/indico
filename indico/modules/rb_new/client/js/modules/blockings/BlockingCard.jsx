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

import moment from 'moment';
import React from 'react';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Item} from 'semantic-ui-react';
import roomsSpriteURL from 'indico-url:rooms_new.sprite';
import {PluralTranslate} from 'indico/react/i18n';
import {TooltipIfTruncated} from 'indico/react/components';
import SpriteImage from '../../components/SpriteImage';
import * as configSelectors from '../../common/config/selectors';

import './BlockingCard.module.scss';


class BlockingCard extends React.Component {
    static propTypes = {
        blocking: PropTypes.object.isRequired,
        onClick: PropTypes.func.isRequired,
        roomsSpriteToken: PropTypes.string.isRequired
    };

    renderCardHeader() {
        const {blocking} = this.props;
        const {blockedRooms} = blocking;

        if (blockedRooms.length === 1) {
            return blockedRooms[0].room.name;
        }

        return PluralTranslate.string('1 room', '{count} rooms', blockedRooms.length, {count: blockedRooms.length});
    }

    render() {
        const {blocking, onClick, roomsSpriteToken} = this.props;
        const {blockedRooms} = blocking;

        return (
            <Item.Group onClick={onClick} styleName="blocking-item">
                <Item key={blocking.id}>
                    <div className="image">
                        <SpriteImage src={roomsSpriteURL({version: roomsSpriteToken})}
                                     pos={blockedRooms[0].room.spritePosition}
                                     origin="0 0"
                                     scale="0.5" />
                    </div>
                    <Item.Content>
                        <Item.Header>{this.renderCardHeader()}</Item.Header>
                        <Item.Meta>
                            {moment(blocking.startDate).format('ll')} - {moment(blocking.endDate).format('ll')}
                        </Item.Meta>
                        <Item.Description>
                            <TooltipIfTruncated>
                                <div styleName="blocking-reason">
                                    {blocking.reason}
                                </div>
                            </TooltipIfTruncated>
                        </Item.Description>
                    </Item.Content>
                </Item>
            </Item.Group>
        );
    }
}

export default connect(
    (state) => ({
        roomsSpriteToken: configSelectors.getRoomsSpriteToken(state)
    })
)(BlockingCard);
