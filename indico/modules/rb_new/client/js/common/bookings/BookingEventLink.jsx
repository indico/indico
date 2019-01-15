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
import {Message, Placeholder, Segment, Icon} from 'semantic-ui-react';
import getLinkedObjectDataURL from 'indico-url:rooms_new.linked_object_data';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';

import './BookingEventLink.module.scss';


export default class BookingEventLink extends React.PureComponent {
    static propTypes = {
        eventId: PropTypes.number.isRequired,
    };

    state = {
        loaded: false,
        data: {},
    };

    componentDidMount() {
        const {eventId} = this.props;
        this.fetchEventData(eventId);
    }

    async fetchEventData(eventId) {
        let response;
        try {
            response = await indicoAxios.get(getLinkedObjectDataURL({type: 'event', id: eventId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        this.setState({
            loaded: true,
            data: camelizeKeys(response.data)
        });
    }

    renderEventInfo(data) {
        const {url, title, canAccess} = data;
        return (
            <Message icon color="teal">
                <Icon name="linkify" />
                <Message.Content>
                    {canAccess ? (
                        <>
                            <Translate>This booking is linked to an event:</Translate>
                            <div styleName="booking-event-link">
                                <a href={url}>{title}</a>
                            </div>
                        </>
                    ) : (
                        <Translate>This booking is linked to an event.</Translate>
                    )}
                </Message.Content>
            </Message>
        );
    }

    render() {
        const {loaded, data} = this.state;
        return (
            loaded ? (
                this.renderEventInfo(data)
            ) : (
                <Segment>
                    <Placeholder fluid>
                        <Placeholder.Header image>
                            <Placeholder.Line length="full" />
                            <Placeholder.Line length="full" />
                        </Placeholder.Header>
                    </Placeholder>
                </Segment>
            )
        );
    }
}
