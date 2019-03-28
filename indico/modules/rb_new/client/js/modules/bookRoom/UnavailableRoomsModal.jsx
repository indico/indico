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
import {Dimmer, Icon, Loader, Modal, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import * as selectors from './selectors';
import * as unavailableRoomsActions from './actions';
import {BookingTimelineComponent} from './BookingTimeline';
import {DateNavigator, TimelineLegend} from '../../common/timeline';


class UnavailableRoomsModal extends React.Component {
    static propTypes = {
        datePicker: PropTypes.object.isRequired,
        availability: PropTypes.array,
        filters: PropTypes.object.isRequired,
        isFetching: PropTypes.bool.isRequired,
        timelineDatePicker: PropTypes.object.isRequired,
        isTimelineVisible: PropTypes.bool.isRequired,
        onClose: PropTypes.func,
        actions: PropTypes.exact({
            fetchUnavailableRooms: PropTypes.func.isRequired,
            setDate: PropTypes.func.isRequired,
            setMode: PropTypes.func.isRequired,
            initTimeline: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        availability: [],
        onClose: null,
    };

    componentDidMount() {
        const {
            actions: {fetchUnavailableRooms, initTimeline},
            filters,
            timelineDatePicker,
            isTimelineVisible
        } = this.props;
        const selectedDate = isTimelineVisible ? timelineDatePicker.selectedDate : filters.dates.startDate;
        const mode = isTimelineVisible ? timelineDatePicker.mode : 'days';

        fetchUnavailableRooms(filters);
        initTimeline(selectedDate, mode);
    }

    render() {
        const {availability, actions, isFetching, onClose, datePicker} = this.props;
        if (availability.length === 0) {
            return <Dimmer active page><Loader /></Dimmer>;
        }

        const legendLabels = [
            {label: Translate.string('Available'), style: 'available'},
            {label: Translate.string('Booked'), style: 'booking'},
            {label: Translate.string('Pre-Booked'), style: 'pre-booking'},
            {label: Translate.string('Invalid occurrence'), style: 'conflicting-candidate'},
            {label: Translate.string('Conflict'), style: 'conflict'},
            {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict'},
            {label: Translate.string('Blocked'), style: 'blocking'},
            {label: Translate.string('Blocked (allowed)'), style: 'overridable-blocking'},
            {label: Translate.string('Not bookable'), style: 'unbookable'}
        ];

        return (
            <Modal open onClose={onClose} size="large" closeIcon>
                <Modal.Header className="legend-header">
                    <Translate>Unavailable Rooms</Translate>
                    <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                           content={<TimelineLegend labels={legendLabels} compact />} />
                    <DateNavigator {...datePicker}
                                   disabled={isFetching || !availability.length}
                                   onModeChange={actions.setMode}
                                   onDateChange={actions.setDate} />
                </Modal.Header>
                <Modal.Content>
                    <BookingTimelineComponent isLoading={isFetching}
                                              availability={availability}
                                              datePicker={datePicker}
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
        datePicker: selectors.getUnavailableDatePicker(state),
        timelineDatePicker: selectors.getTimelineDatePicker(state),
        isTimelineVisible: selectors.isTimelineVisible(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchUnavailableRooms: unavailableRoomsActions.fetchUnavailableRooms,
            setDate: (date) => unavailableRoomsActions.setUnavailableNavDate(serializeDate(date)),
            setMode: unavailableRoomsActions.setUnavailableNavMode,
            initTimeline: unavailableRoomsActions.initUnavailableTimeline,
        }, dispatch)
    })
)(UnavailableRoomsModal);
