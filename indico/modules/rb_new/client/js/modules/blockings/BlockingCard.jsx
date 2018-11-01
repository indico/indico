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
import PropTypes from 'prop-types';
import {Card} from 'semantic-ui-react';
import {TooltipIfTruncated} from 'indico/react/components';
import {Translate, Param, PluralTranslate} from 'indico/react/i18n';
import SpriteImage from '../../components/SpriteImage';

import './BlockingCard.module.scss';


export default class BlockingCard extends React.Component {
    static propTypes = {
        blocking: PropTypes.object.isRequired,
        onClick: PropTypes.func.isRequired
    };

    renderCardHeader() {
        const {blocking} = this.props;
        const {blockedRooms} = blocking;

        if (blockedRooms.length === 1) {
            return blockedRooms[0].room.name;
        }

        return PluralTranslate.string('1 room', '{count} rooms', blockedRooms.length, {count: blockedRooms.length});
    }

    renderDate() {
        const {blocking: {startDate, endDate}} = this.props;
        if (startDate === endDate) {
            return moment(startDate).format('ll');
        } else {
            return (
                <>
                    {moment(startDate).format('ll')} - {moment(endDate).format('ll')}
                </>
            );
        }
    }

    render() {
        const {blocking, onClick} = this.props;
        const {blockedRooms} = blocking;

        return (
            <Card onClick={onClick} styleName="blocking-item" key={blocking.id}>
                <div className="image">
                    <SpriteImage key={blockedRooms[0].room.id}
                                 pos={blockedRooms[0].room.spritePosition} />
                </div>
                <Card.Content>
                    <Card.Header>{this.renderCardHeader()}</Card.Header>
                    <Card.Meta>{this.renderDate()}</Card.Meta>
                    <Card.Description>
                        <TooltipIfTruncated>
                            <div styleName="blocking-reason">
                                {blocking.reason}
                            </div>
                        </TooltipIfTruncated>
                    </Card.Description>
                </Card.Content>
                <Card.Content extra>
                    <Translate>
                        Created by <Param name="createdBy" value={blocking.createdBy} />
                    </Translate>
                </Card.Content>
            </Card>
        );
    }
}
