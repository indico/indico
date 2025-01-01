// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Button, Confirm, Dropdown, Form, Icon} from 'semantic-ui-react';

import {PopoverDropdownMenu} from 'indico/react/components';
import {FinalTextArea} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {actions as bookingsActions} from '../bookings';

import SingleRoomTimelineModal from './SingleRoomTimelineModal';

import './RowActionsDropdown.module.scss';

class RowActionsDropdown extends React.Component {
  static propTypes = {
    booking: PropTypes.object,
    date: PropTypes.object,
    room: PropTypes.object,
    actions: PropTypes.exact({
      changeBookingOccurrenceState: PropTypes.func.isRequired,
      fetchBookingDetails: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    booking: null,
    date: null,
    room: null,
  };

  constructor(props) {
    super(props);
    this.dropdownIconRef = React.createRef();
  }

  state = {
    actionInProgress: false,
    activeConfirmation: null,
    activeRoomTimeline: false,
    dropdownOpen: false,
  };

  hideConfirm = () => {
    this.setState({activeConfirmation: null});
  };

  showConfirm = type => {
    this.setState({activeConfirmation: type});
  };

  showRoomTimeline = () => {
    this.setState({activeRoomTimeline: true});
  };

  hideRoomTimeline = () => {
    this.setState({activeRoomTimeline: false});
  };

  changeOccurrenceState = async (action, data = {}) => {
    const {
      date,
      booking: {id},
      actions: {changeBookingOccurrenceState, fetchBookingDetails},
    } = this.props;
    const serializedDate = serializeDate(date);
    this.setState({actionInProgress: true});
    await changeBookingOccurrenceState(id, serializedDate, action, data);
    await fetchBookingDetails(id);
    this.setState({actionInProgress: false});
  };

  handleButtonClick = () => {
    this.setState({
      dropdownOpen: true,
    });
  };

  renderRejectionForm = ({
    handleSubmit,
    hasValidationErrors,
    submitSucceeded,
    submitting,
    pristine,
  }) => {
    const {date} = this.props;
    const serializedDate = serializeDate(date, 'L');
    return (
      <Form styleName="rejection-form" onSubmit={handleSubmit}>
        <div styleName="form-description">
          <Translate>
            Are you sure you want to reject this occurrence (
            <Param name="date" value={serializedDate} />
            )?
          </Translate>
        </div>
        <FinalTextArea
          name="reason"
          placeholder={Translate.string('Provide the rejection reason')}
          disabled={submitSucceeded}
          rows={2}
          required
          autoFocus
        />
        <Button
          type="submit"
          disabled={submitting || pristine || hasValidationErrors || submitSucceeded}
          loading={submitting}
          floated="right"
          primary
        >
          <Translate>Reject</Translate>
        </Button>
      </Form>
    );
  };

  render() {
    const {activeConfirmation, activeRoomTimeline, actionInProgress, dropdownOpen} = this.state;
    const {booking, date, room} = this.props;
    const serializedDate = serializeDate(date, 'L');
    let canCancel, canReject;
    const rejectionForm = (
      <FinalForm
        onSubmit={data => this.changeOccurrenceState('reject', data)}
        render={this.renderRejectionForm}
      />
    );

    if (booking) {
      ({canCancel, canReject} = booking.occurrences.bookings[serializeDate(date)][0]);
    }

    if (!canCancel && !canReject && !room) {
      return null;
    }

    const styleName = dropdownOpen ? 'dropdown-button open' : 'dropdown-button';
    const trigger = (
      <Button styleName={styleName} loading={actionInProgress}>
        <Button.Content>
          <Icon name="ellipsis horizontal" size="large" />
        </Button.Content>
      </Button>
    );

    return (
      <div styleName="actions-dropdown">
        <PopoverDropdownMenu
          onOpen={this.handleButtonClick}
          onClose={() => this.setState({dropdownOpen: false})}
          open={dropdownOpen}
          trigger={trigger}
          placement="bottom"
        >
          {canCancel && (
            <Dropdown.Item
              icon="times"
              text={Translate.string('Cancel occurrence')}
              onClick={() => this.showConfirm('cancel')}
            />
          )}
          {canReject && (
            <Dropdown.Item
              icon="times circle"
              text={Translate.string('Reject occurrence')}
              onClick={() => this.showConfirm('reject')}
            />
          )}
          {room && (
            <Dropdown.Item
              icon="list"
              text={Translate.string('Show room timeline')}
              onClick={() => this.showRoomTimeline(room)}
            />
          )}
        </PopoverDropdownMenu>
        <Confirm
          header={Translate.string('Confirm cancellation')}
          content={Translate.string(
            'Are you sure you want to cancel this occurrence ({serializedDate})?',
            {
              serializedDate,
            }
          )}
          confirmButton={<Button content={Translate.string('Cancel occurrence')} negative />}
          cancelButton={Translate.string('Close')}
          open={activeConfirmation === 'cancel'}
          onCancel={this.hideConfirm}
          onConfirm={() => {
            this.changeOccurrenceState('cancel');
            this.hideConfirm();
          }}
        />
        <Confirm
          header={Translate.string('Confirm rejection')}
          content={rejectionForm}
          confirmButton={null}
          cancelButton={Translate.string('Close')}
          open={activeConfirmation === 'reject'}
          onCancel={this.hideConfirm}
        />
        {room && (
          <SingleRoomTimelineModal
            open={activeRoomTimeline}
            onClose={this.hideRoomTimeline}
            room={room}
          />
        )}
      </div>
    );
  }
}

export default connect(
  null,
  dispatch => ({
    actions: bindActionCreators(
      {
        changeBookingOccurrenceState: bookingsActions.changeBookingOccurrenceState,
        fetchBookingDetails: bookingsActions.fetchBookingDetails,
      },
      dispatch
    ),
  })
)(RowActionsDropdown);
