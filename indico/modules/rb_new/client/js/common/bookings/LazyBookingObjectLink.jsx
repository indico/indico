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

import getLinkedObjectDataURL from 'indico-url:rooms_new.linked_object_data';

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Placeholder, Segment} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import BookingObjectLink from './BookingObjectLink';

/**
 * `LazyBookingObjectLink` wraps `BookingObjectLink` and loads the data
 * of the object on demand.
 */
export default class LazyBookingObjectLink extends React.PureComponent {
    static propTypes = {
        type: PropTypes.oneOf(['event', 'contribution', 'sessionBlock']).isRequired,
        id: PropTypes.number.isRequired,
        /** Whether it is a pending link or the booking is already linked */
        pending: PropTypes.bool,
    };

    static defaultProps = {
        pending: false,
    };

    state = {
        loaded: false,
        link: {},
        canAccess: false,
    };

    componentDidMount() {
        const {type, id} = this.props;
        this.fetchLinkedObjectData(type, id);
    }

    async fetchLinkedObjectData(type, id) {
        let response;
        try {
            response = await indicoAxios.get(getLinkedObjectDataURL({type: _.snakeCase(type), id}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        const {canAccess, ...data} = camelizeKeys(response.data);
        this.setState({
            loaded: true,
            link: canAccess ? {type, ...data} : null,
            canAccess,
        });
    }

    render() {
        const {pending} = this.props;
        const {loaded, link, canAccess} = this.state;
        if (loaded && !canAccess) {
            return null;
        } else if (loaded) {
            return <BookingObjectLink pending={pending} link={link} />;
        } else {
            return (
                <Segment>
                    <Placeholder fluid>
                        <Placeholder.Header image>
                            <Placeholder.Line length="full" />
                            <Placeholder.Line length="full" />
                        </Placeholder.Header>
                    </Placeholder>
                </Segment>
            );
        }
    }
}
