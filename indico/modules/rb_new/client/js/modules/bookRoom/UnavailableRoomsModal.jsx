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
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Dimmer, Loader, Modal} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import * as selectors from './selectors';
import * as actions from './actions';
import {BookingTimelineComponent} from './BookingTimeline';


class UnavailableRoomsModal extends React.Component {
    static propTypes = {
        actions: PropTypes.object.isRequired,
        availability: PropTypes.array,
        filters: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        dateRange: PropTypes.array,
        onClose: PropTypes.func
    };

    static defaultProps = {
        availability: [],
        onClose: null,
        dateRange: null,
    };

    componentDidMount() {
        const {actions: {fetchUnavailableRooms}, filters} = this.props;
        fetchUnavailableRooms(filters);
    }

    render() {
        const {availability, dateRange, filters, isFetching, onClose} = this.props;
        if (!dateRange || availability.length === 0) {
            return <Dimmer active page><Loader /></Dimmer>;
        }

        return (
            <Modal open onClose={onClose} size="large" closeIcon>
                <Modal.Header>
                    <Translate>Unavailable Rooms</Translate>
                </Modal.Header>
                <Modal.Content scrolling>
                    <BookingTimelineComponent isFetching={isFetching}
                                              isFetchingRooms={false}
                                              recurrenceType={filters.recurrence.type}
                                              availability={availability}
                                              dateRange={dateRange} />
                </Modal.Content>
            </Modal>
        );
    }
}

export default connect(
    state => ({
        availability: selectors.getUnavailableRoomInfo(state),
        filters: selectors.getFilters(state),
        isFetching: selectors.isFetchingUnavailableRooms(state),
        dateRange: selectors.getAvailabilityDateRange(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchUnavailableRooms: actions.fetchUnavailableRooms
        }, dispatch)
    })
)(UnavailableRoomsModal);
