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
import {Message, Icon} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {linkDataShape} from '../linking';

import './BookingObjectLink.module.scss';

/**
 * `BookingObjectLink` displays a message informing if the booking is
 * linked or will be linked to an event, contribution or session block.
 */
export default class BookingObjectLink extends React.PureComponent {
    static propTypes = {
        link: linkDataShape.isRequired,
        /** Whether it is a pending link or the booking is already linked */
        pending: PropTypes.bool,
    };

    static defaultProps = {
        pending: false,
    };

    render() {
        const {pending, link: {type, title, eventURL, eventTitle}} = this.props;
        const pendingMessages = {
            event: Translate.string('This booking will be linked to an event:'),
            contribution: Translate.string('This booking will be linked to a contribution:'),
            sessionBlock: Translate.string('This booking will be linked to a session block:'),
        };
        const linkedMessages = {
            event: Translate.string('This booking is linked to an event:'),
            contribution: Translate.string('This booking is linked to a contribution:'),
            sessionBlock: Translate.string('This booking is linked to a session block:'),
        };
        return (
            <Message icon color="teal">
                <Icon name="linkify" />
                <Message.Content>
                    {pending ? pendingMessages[type] : linkedMessages[type]}
                    <div styleName="object-link">
                        {type === 'event'
                            ? <a href={eventURL}><em>{title}</em></a>
                            : <span><em>{title}</em> (<a href={eventURL}>{eventTitle}</a>)</span>
                        }
                    </div>
                </Message.Content>
            </Message>
        );
    }
}
