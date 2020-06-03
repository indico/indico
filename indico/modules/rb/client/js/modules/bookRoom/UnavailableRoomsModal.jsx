// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Dimmer, Icon, Loader, Modal, Popup} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import {Responsive} from 'indico/react/util';
import * as selectors from './selectors';
import * as unavailableRoomsActions from './actions';
import {BookingTimelineComponent} from './BookingTimeline';
import {DateNavigator, TimelineLegend} from '../../common/timeline';
import {actions as bookingsActions} from '../../common/bookings';
import {getOccurrenceTypes, transformToLegendLabels} from '../../util';

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
      openBookingDetails: PropTypes.func.isRequired,
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
      isTimelineVisible,
    } = this.props;

    const {selectedDate, mode} = timelineDatePicker;
    const initialDate = isTimelineVisible && selectedDate ? selectedDate : filters.dates.startDate;
    const initialMode = isTimelineVisible && mode ? mode : 'days';

    fetchUnavailableRooms(filters);
    initTimeline(initialDate, initialMode);
  }

  getLegendLabels = availability => {
    const occurrenceTypes = availability.reduce(
      (types, [, day]) => _.union(types, getOccurrenceTypes(day)),
      []
    );
    return transformToLegendLabels(occurrenceTypes);
  };

  render() {
    const {availability, actions, isFetching, onClose, datePicker} = this.props;
    if (availability.length === 0) {
      return (
        <Dimmer active page>
          <Loader />
        </Dimmer>
      );
    }

    const timelineHeader = (
      <>
        <Popup
          trigger={<Icon name="info circle" className="legend-info-icon" />}
          content={<TimelineLegend labels={this.getLegendLabels(availability)} compact />}
        />
        <DateNavigator
          {...datePicker}
          disabled={isFetching || !availability.length}
          onModeChange={actions.setMode}
          onDateChange={actions.setDate}
        />
      </>
    );

    return (
      <Modal open onClose={onClose} size="large" closeIcon>
        <Modal.Header className="legend-header">
          <Translate>Unavailable Rooms</Translate>
          <Responsive.Portrait orElse={timelineHeader}>
            <Responsive.Tablet andLarger>{timelineHeader}</Responsive.Tablet>
          </Responsive.Portrait>
        </Modal.Header>
        <Modal.Content>
          <BookingTimelineComponent
            isLoading={isFetching}
            availability={availability}
            datePicker={datePicker}
            fixedHeight="70vh"
            onClickReservation={actions.openBookingDetails}
            setMode={actions.setMode}
            setDate={actions.setDate}
          />
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
    actions: bindActionCreators(
      {
        fetchUnavailableRooms: unavailableRoomsActions.fetchUnavailableRooms,
        setDate: date => unavailableRoomsActions.setUnavailableNavDate(serializeDate(date)),
        setMode: unavailableRoomsActions.setUnavailableNavMode,
        initTimeline: unavailableRoomsActions.initUnavailableTimeline,
        openBookingDetails: bookingsActions.openBookingDetails,
      },
      dispatch
    ),
  })
)(UnavailableRoomsModal);
