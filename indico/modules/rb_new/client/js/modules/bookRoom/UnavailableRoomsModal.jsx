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
import {serializeDate} from 'indico/utils/date';
import * as selectors from './selectors';
import * as unavailableRoomsActions from './actions';
import {BookingTimelineComponent} from './BookingTimeline';
import {TimelineHeader} from '../../common/timeline';


class UnavailableRoomsModal extends React.Component {
    static propTypes = {
        datePicker: PropTypes.object.isRequired,
        actions: PropTypes.exact({
            fetchUnavailableRooms: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            setMode: PropTypes.func.isRequired
        }).isRequired,
        availability: PropTypes.array,
        filters: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        onClose: PropTypes.func
    };

    static defaultProps = {
        availability: [],
        onClose: null,
    };

    componentDidMount() {
        const {actions: {fetchUnavailableRooms}, filters} = this.props;
        fetchUnavailableRooms(filters);
    }

    render() {
        const {availability, actions, isFetching, onClose, datePicker, filters: {dates: {startDate}}} = this.props;
        // If we're in "timeline" mode, use the datepicker, otherwise the current starting day
        const picker = datePicker.selectedDate ? datePicker : {...datePicker, selectedDate: startDate};

        if (availability.length === 0) {
            return <Dimmer active page><Loader /></Dimmer>;
        }

        const legendLabels = [
            {label: Translate.string('Available'), color: 'green'},
            {label: Translate.string('Booked'), color: 'orange'},
            {label: Translate.string('Pre-Booking'), style: 'pre-booking'},
            {label: Translate.string('Conflict'), color: 'red'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];

        return (
            <Modal open onClose={onClose} size="large" closeIcon>
                <Modal.Header>
                    <Translate>Unavailable Rooms</Translate>
                </Modal.Header>
                <Modal.Content>
                    <TimelineHeader datePicker={datePicker}
                                    disableDatePicker={isFetching || !availability.length}
                                    onModeChange={actions.setMode}
                                    onDateChange={actions.setDate}
                                    legendLabels={legendLabels} />
                    <BookingTimelineComponent isLoading={isFetching}
                                              availability={availability}
                                              datePicker={picker}
                                              fixedHeight="70vh" />
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
        datePicker: selectors.getTimelineDatePicker(state)
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchUnavailableRooms: unavailableRoomsActions.fetchUnavailableRooms,
            setDate: date => unavailableRoomsActions.setUnavailableDate(serializeDate(date)),
            setMode: unavailableRoomsActions.setUnavailableMode
        }, dispatch)
    })
)(UnavailableRoomsModal);
