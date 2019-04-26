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

        const {selectedDate, mode} = timelineDatePicker;
        const initialDate = isTimelineVisible && selectedDate ? selectedDate : filters.dates.startDate;
        const initialMode = isTimelineVisible && mode ? mode : 'days';

        fetchUnavailableRooms(filters);
        initTimeline(initialDate, initialMode);
    }

    transformToLabel = (type) => {
        switch (type) {
            case 'candidates':
                return {label: Translate.string('Available'), style: 'available', order: 1};
            case 'bookings':
                return {label: Translate.string('Booked'), style: 'booking', order: 2};
            case 'preBookings':
                return {label: Translate.string('Pre-Booked'), style: 'pre-booking', order: 3};
            case 'conflicts':
                return {label: Translate.string('Conflict'), style: 'conflict', order: 4};
            case 'preConflicts':
                return {label: Translate.string('Conflict with Pre-Booking'), style: 'pre-booking-conflict', order: 5};
            case 'conflictingCandidates':
                return {label: Translate.string('Invalid occurrence'), style: 'conflicting-candidate', order: 6};
            case 'blockings':
                return {label: Translate.string('Blocked'), style: 'blocking', order: 7};
            case 'overridableBlockings':
                return {label: Translate.string('Blocked (allowed)'), style: 'overridable-blocking', order: 8};
            case 'nonbookablePeriods':
            case 'unbookableHours':
                return {label: Translate.string('Not bookable'), style: 'unbookable', order: 9};
            default:
                return undefined;
        }
    };

    getLegendLabels = (availability) => {
        const legendLabels = [];
        availability.forEach(([, day]) => {
            Object.entries(day).forEach(([type, occurrences]) => {
                if (occurrences && Object.keys(occurrences).length > 0) {
                    const label = this.transformToLabel(type);
                    if (label && !legendLabels.some(lab => _.isEqual(lab, label))) {
                        legendLabels.push(label);
                    }
                }
            });
        });
        return legendLabels.sort((a, b) => a.order - b.order);
    };

    render() {
        const {availability, actions, isFetching, onClose, datePicker} = this.props;
        if (availability.length === 0) {
            return <Dimmer active page><Loader /></Dimmer>;
        }

        return (
            <Modal open onClose={onClose} size="large" closeIcon>
                <Modal.Header className="legend-header">
                    <Translate>Unavailable Rooms</Translate>
                    <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                           content={<TimelineLegend labels={this.getLegendLabels(availability)} compact />} />
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
