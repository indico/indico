/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import React, {useEffect} from 'react';
import moment from 'moment';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {Modal, Icon, Dimmer, Loader, Popup} from 'semantic-ui-react';

import * as bookRoomSelectors from '../../modules/bookRoom/selectors';
import {actions as bookRoomActions} from '../../modules/bookRoom';
import TimelineLegend from './TimelineLegend';
import {DailyTimelineContent} from '.';

import './SingleRoomTimelineModal.module.scss';


const _SingleRoomTimelineContent = props => {
    const {availability, availabilityLoading, room, filters, actions: {fetchAvailability}} = props;
    useEffect(() => {
        fetchAvailability(room, filters);
    }, [fetchAvailability, filters, room]);

    const isLoaded = !_.isEmpty(availability) && !availabilityLoading;
    const dimmer = <Dimmer active page styleName="dimmer"><Loader /></Dimmer>;
    const _getRowSerializer = (day) => {
        return ({bookings, preBookings, candidates, conflictingCandidates, nonbookablePeriods, unbookableHours,
                 blockings, conflicts, preConflicts}) => ({
            availability: {
                candidates: (candidates[day] || []).map((candidate) => (
                    {...candidate, bookable: false})
                ) || [],
                conflictingCandidates: (conflictingCandidates[day] || []).map((candidate) => (
                    {...candidate, bookable: false}
                )) || [],
                preBookings: preBookings[day] || [],
                bookings: bookings[day] || [],
                conflicts: conflicts[day] || [],
                preConflicts: preConflicts[day] || [],
                nonbookablePeriods: nonbookablePeriods[day] || [],
                unbookableHours: unbookableHours || [],
                blockings: blockings[day] || []
            },
            label: moment(day).format('L'),
            key: day,
            conflictIndicator: true,
            room
        });
    };
    const renderRoomTimeline = () => {
        const {dateRange} = availability;
        const rows = dateRange.map((day) => _getRowSerializer(day)(availability));
        return <DailyTimelineContent rows={rows} fixedHeight={rows.length > 1 ? '70vh' : null} />;
    };

    return isLoaded ? renderRoomTimeline() : dimmer;
};

_SingleRoomTimelineContent.propTypes = {
    room: PropTypes.object.isRequired,
    availability: PropTypes.object,
    availabilityLoading: PropTypes.bool.isRequired,
    filters: PropTypes.object.isRequired,
    actions: PropTypes.exact({
        fetchAvailability: PropTypes.func.isRequired,
    }).isRequired,
};

_SingleRoomTimelineContent.defaultProps = {
    availability: {},
};

const SingleRoomTimelineContent = connect(
    state => ({
        filters: bookRoomSelectors.getFilters(state),
        availability: bookRoomSelectors.getBookingFormAvailability(state),
        availabilityLoading: bookRoomSelectors.isFetchingFormTimeline(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            fetchAvailability: bookRoomActions.fetchBookingAvailability,
        }, dispatch)
    }),
)(React.memo(_SingleRoomTimelineContent));


const SingleRoomTimelineModal = props => {
    const {open, title, onClose, room, legendLabels} = props;
    return (
        <Modal open={open}
               onClose={onClose}
               size="large" closeIcon>
            <Modal.Header className="legend-header">
                {title ? title : room.name}
                <Popup trigger={<Icon name="info circle" className="legend-info-icon" />}
                       content={<TimelineLegend labels={legendLabels} compact />} />
            </Modal.Header>
            <Modal.Content>
                <SingleRoomTimelineContent room={room} />
            </Modal.Content>
        </Modal>
    );
};

SingleRoomTimelineModal.propTypes = {
    open: PropTypes.bool,
    title: PropTypes.node,
    onClose: PropTypes.func,
    legendLabels: PropTypes.array,
    room: PropTypes.object.isRequired,
};

SingleRoomTimelineModal.defaultProps = {
    open: false,
    title: '',
    onClose: () => {},
    legendLabels: [],
};

export default SingleRoomTimelineModal;
