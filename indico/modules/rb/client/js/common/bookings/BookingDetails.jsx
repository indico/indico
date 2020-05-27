// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import bookingLinkURL from 'indico-url:rb.booking_link';

import _ from 'lodash';
import moment from 'moment';
import React from 'react';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {
  Button,
  Confirm,
  Form,
  Grid,
  Header,
  Icon,
  Label,
  List,
  Message,
  Modal,
  Popup,
} from 'semantic-ui-react';

import {toMoment, serializeDate} from 'indico/utils/date';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {FinalCheckbox, FinalTextArea} from 'indico/react/forms';
import {Responsive} from 'indico/react/util';
import {ClipboardButton} from 'indico/react/components';
import {DailyTimelineContent, TimelineLegend} from '../timeline';
import {
  getRecurrenceInfo,
  PopupParam,
  getOccurrenceTypes,
  transformToLegendLabels,
} from '../../util';
import RoomBasicDetails from '../../components/RoomBasicDetails';
import RoomKeyLocation from '../../components/RoomKeyLocation';
import TimeInformation from '../../components/TimeInformation';
import {openModal} from '../../actions';
import LazyBookingObjectLink from './LazyBookingObjectLink';
import * as bookingsSelectors from './selectors';
import * as bookingsActions from './actions';

import './BookingDetails.module.scss';

class BookingDetails extends React.Component {
  static propTypes = {
    onClose: PropTypes.func,
    editButton: PropTypes.func.isRequired,
    booking: PropTypes.object.isRequired,
    bookingStateChangeInProgress: PropTypes.bool.isRequired,
    actions: PropTypes.exact({
      deleteBooking: PropTypes.func.isRequired,
      changeBookingOccurrenceState: PropTypes.func,
      changeBookingState: PropTypes.func.isRequired,
      openBookingDetails: PropTypes.func.isRequired,
      fetchBookingDetails: PropTypes.func.isRequired,
    }).isRequired,
    cancelDate: PropTypes.string,
  };

  static defaultProps = {
    onClose: () => {},
    cancelDate: null,
  };

  state = {
    occurrencesVisible: false,
    activeConfirmation: null,
    acceptanceFormVisible: false,
    preBookingConflicts: {
      warningVisible: false,
      concurrentBookings: [],
      acceptanceData: null,
    },
  };

  showAcceptanceForm = () => {
    this.setState({acceptanceFormVisible: true});
  };

  hideAcceptanceForm = () => {
    this.setState({acceptanceFormVisible: false});
  };

  showOccurrences = () => {
    this.setState({occurrencesVisible: true});
  };

  hideOccurrences = () => {
    this.setState({occurrencesVisible: false});
  };

  hidePreBookingWarning = () => {
    this.setState({
      preBookingConflicts: {
        warningVisible: false,
        concurrentBookings: [],
        acceptanceData: null,
      },
    });
  };

  renderBookedFor = bookedForUser => {
    const {fullName: bookedForName, email: bookedForEmail, phone: bookedForPhone} = bookedForUser;
    return (
      <>
        <Header>
          <Icon name="user" />
          <Translate>Booked for</Translate>
        </Header>
        <div>{bookedForName}</div>
        {bookedForPhone && (
          <div>
            <Icon name="phone" />
            {bookedForPhone}
          </div>
        )}
        {bookedForEmail && (
          <div>
            <Icon name="mail" />
            {bookedForEmail}
          </div>
        )}
      </>
    );
  };

  renderPreBookingWarning = () => {
    const {bookingStateChangeInProgress} = this.props;
    const {
      actionInProgress,
      preBookingConflicts: {warningVisible, concurrentBookings, acceptanceData},
    } = this.state;
    const items = concurrentBookings.map(booking => {
      const reservation = booking.reservation;
      const startDate = serializeDate(toMoment(booking.start_dt), 'L LT');
      const endDate = serializeDate(toMoment(booking.end_dt), 'LT');
      return (
        <List.Item key={reservation.id}>
          <a
            href={bookingLinkURL({booking_id: reservation.id})}
            target="_blank"
            rel="noopener noreferrer"
          >
            {startDate} - {endDate}
          </a>{' '}
          <Translate>
            by <Param name="user" value={reservation.booked_for_name} />
          </Translate>{' '}
          ({reservation.booking_reason})
        </List.Item>
      );
    });
    return (
      <Modal open={warningVisible} size="small" onClose={this.hidePreBookingWarning}>
        <Modal.Header>
          <Translate>Warning</Translate>
        </Modal.Header>
        <Modal.Content>
          <Translate>
            There is more than one booking request during this time. Accepting this booking will
            automatically reject the following:
          </Translate>
          <div styleName="concurrent-reservations">
            <List divided styleName="concurrent-reservations-list">
              {items}
            </List>
          </div>
        </Modal.Content>
        <Modal.Actions>
          <Button
            content={Translate.string('Close without accepting')}
            onClick={this.hidePreBookingWarning}
          />
          <Button
            icon="check circle"
            onClick={() => {
              this.changeState('approve', {...acceptanceData, force: true});
              this.hidePreBookingWarning();
            }}
            loading={actionInProgress === 'approve' && bookingStateChangeInProgress}
            disabled={bookingStateChangeInProgress}
            content={Translate.string('Accept anyway')}
            positive
          />
        </Modal.Actions>
      </Modal>
    );
  };

  renderCancelOccurrence = (bookings, id) => {
    const {
      actions: {openBookingDetails},
    } = this.props;
    const {cancelDate} = this.props;
    const serializedDate = serializeDate(cancelDate, 'L');
    if (cancelDate === null) {
      return null;
    } else if (bookings[cancelDate] === undefined || bookings[cancelDate].length === 0) {
      return (
        <Modal open size="tiny" onClose={() => openBookingDetails(id)}>
          <Modal.Header>Cancellation not possible</Modal.Header>
          <Modal.Content>
            <Translate>
              There is no occurrence on this date (
              <Param name="date" value={serializedDate} />
              ).
            </Translate>
          </Modal.Content>
          <Modal.Actions>
            <Button content={Translate.string('Close')} onClick={() => openBookingDetails(id)} />
          </Modal.Actions>
        </Modal>
      );
    } else if (!bookings[cancelDate][0].canCancel) {
      return (
        <Modal open size="tiny" onClose={() => openBookingDetails(id)}>
          <Modal.Header>
            <Translate>Cancellation not possible</Translate>
          </Modal.Header>
          <Modal.Content>
            <Translate>
              The occurrence you chose (
              <Param name="date" value={serializedDate} />) cannot be cancelled.
            </Translate>
          </Modal.Content>
          <Modal.Actions>
            <Button content={Translate.string('Close')} onClick={() => openBookingDetails(id)} />
          </Modal.Actions>
        </Modal>
      );
    } else {
      return (
        <Modal open size="tiny" onClose={() => openBookingDetails(id)}>
          <Modal.Header>
            <Translate>Confirm cancellation</Translate>
          </Modal.Header>
          <Modal.Content>
            <Translate>
              Are you sure you want to cancel this occurrence (
              <Param name="date" value={serializedDate} />
              )?
            </Translate>
          </Modal.Content>
          <Modal.Actions>
            <Button content={Translate.string('Close')} onClick={() => openBookingDetails(id)} />
            <Button
              content={Translate.string('Cancel this occurrence')}
              onClick={async () => {
                await this.cancelOccurrence();
                openBookingDetails(id);
              }}
              negative
            />
          </Modal.Actions>
        </Modal>
      );
    }
  };

  renderReason = reason => (
    <Message info icon styleName="message-icon">
      <Icon name="info" />
      <Message.Content>
        <Message.Header>
          <Translate>Booking reason</Translate>
        </Message.Header>
        {reason}
      </Message.Content>
    </Message>
  );

  _getRowSerializer = day => {
    const {
      booking: {room},
    } = this.props;
    return ({bookings, cancellations, rejections, other}) => ({
      availability: {
        bookings: bookings[day].map(candidate => ({...candidate, bookable: false})) || [],
        cancellations: cancellations[day] || [],
        rejections: rejections[day] || [],
        other: other[day] || [],
      },
      label: moment(day).format('L'),
      key: day,
      room,
    });
  };

  renderTimeline = (occurrences, dateRange) => {
    const {booking} = this.props;
    const rows = dateRange.map(day => this._getRowSerializer(day)(occurrences));
    return (
      <DailyTimelineContent
        rows={rows}
        fixedHeight={rows.length > 1 ? '70vh' : null}
        booking={booking}
        rowActions={{occurrence: true}}
      />
    );
  };

  renderBookingHistory = (editLogs, createdOn, createdByUser) => {
    const {
      actions: {openBookingDetails},
    } = this.props;

    if (createdByUser) {
      const {fullName: createdBy} = createdByUser;
      editLogs = [
        ...editLogs,
        {
          id: 'created',
          timestamp: createdOn,
          info: ['Booking created'],
          userName: createdBy,
        },
      ];
    }
    const items = editLogs.map(log => {
      const {id, timestamp, info, userName} = log;
      let basicInfo = <strong>{info[0]}</strong>;
      let details = null;
      let textInfo = info;
      const match = info[info.length - 1].match(/^booking_link:(\d+)$/);
      if (match) {
        // if the last item is `booking_link:12345` the log entry links to that booking.
        // this is a slightly ugly workaround to allow the otherwise text-only log entries
        // to link to another booking (used for split bookings)
        textInfo = info.slice(0, -1);
        basicInfo = (
          <a
            href={bookingLinkURL({booking_id: match[1]})}
            onClick={evt => {
              evt.preventDefault();
              openBookingDetails(match[1]);
            }}
          >
            {basicInfo}
          </a>
        );
      }
      if (textInfo.length === 2) {
        details = textInfo[1];
      } else if (textInfo.length > 2) {
        details = (
          <ul style={{textAlign: 'left'}}>
            {textInfo.slice(1).map((detail, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={i}>{detail}</li>
            ))}
          </ul>
        );
      }
      const logDate = serializeDate(toMoment(timestamp), 'L LT');
      const popupContent = <span styleName="popup-center">{details}</span>;
      const wrapper = details ? <PopupParam content={popupContent} /> : <span />;
      return (
        <List.Item key={id}>
          <Translate>
            <Param name="date" value={logDate} wrapper={<span styleName="log-date" />} />
            {' - '}
            <Param name="info" wrapper={wrapper} value={basicInfo} /> by{' '}
            <Param name="user" value={userName} />
          </Translate>
        </List.Item>
      );
    });
    return (
      !!items.length && (
        <div styleName="booking-logs">
          <Header>
            <Translate>Booking history</Translate>
          </Header>
          <List divided styleName="log-list">
            {items}
          </List>
        </div>
      )
    );
  };

  renderMessageAfterSplitting = newBookingId => {
    if (newBookingId === undefined) {
      return null;
    }

    const {
      actions: {openBookingDetails},
    } = this.props;
    const link = <a onClick={() => openBookingDetails(newBookingId)} />;
    return (
      <Message color="green">
        <Message.Header>
          <Translate>The booking has been successfully split.</Translate>
        </Message.Header>
        <Translate>
          You can consult your new booking{' '}
          <Param name="link" wrapper={link}>
            here
          </Param>
          .
        </Translate>
      </Message>
    );
  };

  renderBookingStatus = () => {
    const {
      booking: {isPending, isAccepted, isCancelled, isRejected, rejectionReason},
    } = this.props;
    let color, status, icon, message;

    if (isPending) {
      icon = <Icon name="wait" />;
      color = 'yellow';
      status = Translate.string('Pending Confirmation');
      message = Translate.string('This booking is subject to acceptance by the room owner');
    } else if (isCancelled) {
      icon = <Icon name="cancel" />;
      color = 'grey';
      status = Translate.string('Cancelled');
      message = (
        <>
          <Translate>The booking was cancelled.</Translate>
          {!!rejectionReason && (
            <>
              <br />
              <Translate>
                Reason:{' '}
                <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
              </Translate>
            </>
          )}
        </>
      );
    } else if (isRejected) {
      icon = <Icon name="calendar minus" />;
      color = 'red';
      status = Translate.string('Rejected');
      message = (
        <>
          <Translate>The booking was rejected.</Translate>
          {!!rejectionReason && (
            <>
              <br />
              <Translate>
                Reason:{' '}
                <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
              </Translate>
            </>
          )}
        </>
      );
    } else if (isAccepted) {
      icon = <Icon name="checkmark" />;
      color = 'green';
      status = Translate.string('Accepted');
      message = Translate.string('The booking was accepted');
    }

    const label = (
      <Label color={color}>
        {icon}
        {status}
      </Label>
    );

    return <Popup trigger={label} content={message} position="bottom center" />;
  };

  renderDeleteButton = () => {
    const {activeConfirmation} = this.state;
    const {bookingStateChangeInProgress} = this.props;
    return (
      <>
        <Button
          icon="trash"
          onClick={() => this.showConfirm('delete')}
          disabled={bookingStateChangeInProgress}
          negative
          circular
        />
        <Confirm
          header={Translate.string('Confirm deletion')}
          content={Translate.string('Are you sure you want to delete this booking?')}
          confirmButton={<Button content={Translate.string('Delete')} negative />}
          cancelButton={Translate.string('Cancel')}
          open={activeConfirmation === 'delete'}
          onCancel={this.hideConfirm}
          onConfirm={this.deleteBooking}
        />
      </>
    );
  };

  deleteBooking = () => {
    const {
      actions: {deleteBooking},
      booking: {id},
      onClose,
    } = this.props;
    deleteBooking(id);
    onClose();
    this.hideConfirm();
  };

  hideConfirm = () => {
    this.setState({activeConfirmation: null});
  };

  showConfirm = type => {
    this.setState({activeConfirmation: type});
  };

  changeState = (action, data = {}) => {
    const {
      booking: {id},
      actions: {changeBookingState},
    } = this.props;
    const {acceptanceFormVisible} = this.state;
    this.setState({actionInProgress: action});
    return changeBookingState(id, action, data).then(({error}) => {
      if (error && error.message === 'prebooking_collision' && action === 'approve') {
        if (acceptanceFormVisible) {
          this.hideAcceptanceForm();
        }
        this.setState({
          preBookingConflicts: {
            concurrentBookings: error.data,
            acceptanceData: data,
            warningVisible: true,
          },
        });
      }
      this.setState({actionInProgress: null});
    });
  };

  cancelOccurrence = async () => {
    const {
      cancelDate,
      booking: {id},
      actions: {changeBookingOccurrenceState, fetchBookingDetails},
    } = this.props;
    const serializedDate = serializeDate(cancelDate);
    this.setState({actionInProgress: true});
    await changeBookingOccurrenceState(id, serializedDate, 'cancel');
    await fetchBookingDetails(id);
    this.setState({actionInProgress: false});
  };

  getLegendLabels = availability => {
    const inactiveTypes = [
      'blockings',
      'overridableBlockings',
      'nonbookablePeriods',
      'unbookableHours',
    ];
    const occurrenceTypes = getOccurrenceTypes(availability);
    return transformToLegendLabels(occurrenceTypes, inactiveTypes);
  };

  renderActionButtons = (canCancel, canReject, showAccept, occurrenceCount, isAccepted) => {
    const {bookingStateChangeInProgress} = this.props;
    const {actionInProgress, activeConfirmation, acceptanceFormVisible} = this.state;
    const rejectButton = (
      <Button
        type="button"
        icon="remove circle"
        color="red"
        size="small"
        loading={actionInProgress === 'reject' && bookingStateChangeInProgress}
        disabled={bookingStateChangeInProgress}
        content={Translate.string('Reject booking')}
      />
    );

    const acceptWithMessage = (
      <Button
        type="button"
        icon="edit outline"
        styleName="accept-with-message"
        disabled={bookingStateChangeInProgress || acceptanceFormVisible}
      />
    );

    const renderRejectionForm = ({
      handleSubmit,
      hasValidationErrors,
      submitSucceeded,
      submitting,
      pristine,
    }) => {
      return (
        <Form styleName="rejection-form" onSubmit={handleSubmit}>
          <FinalTextArea
            name="reason"
            placeholder={Translate.string('Provide the rejection reason')}
            disabled={submitSucceeded}
            rows={2}
            required
          />
          {isAccepted && occurrenceCount > 1 && (
            <FinalCheckbox
              name="_confirm"
              label={Translate.string(
                'I understand that this will reject all occurrences of the booking.'
              )}
              validate={val =>
                val ? undefined : Translate.string('Please confirm rejecting the booking.')
              }
            />
          )}
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

    const renderAcceptanceForm = ({
      handleSubmit,
      hasValidationErrors,
      submitSucceeded,
      submitting,
    }) => {
      return (
        <Form styleName="rejection-form" onSubmit={handleSubmit}>
          <FinalTextArea
            name="reason"
            placeholder={Translate.string(
              'You can provide an optional message when accepting this booking'
            )}
            disabled={submitSucceeded}
            rows={2}
            autoFocus
          />
          <Button
            type="submit"
            disabled={submitting || hasValidationErrors || submitSucceeded}
            loading={submitting}
            floated="right"
            primary
          >
            <Translate>Accept</Translate>
          </Button>
        </Form>
      );
    };

    return (
      <Modal.Actions>
        {canCancel && (
          <>
            <Button
              type="button"
              icon="cancel"
              size="small"
              onClick={() => this.showConfirm('cancel')}
              loading={actionInProgress === 'cancel' && bookingStateChangeInProgress}
              disabled={bookingStateChangeInProgress}
              content={Translate.string('Cancel booking')}
            />
            <Modal
              open={activeConfirmation === 'cancel'}
              size="small"
              onClose={() => this.hideConfirm()}
            >
              <Modal.Header>
                <Translate>Confirm cancellation</Translate>
              </Modal.Header>
              <Modal.Content>
                <p>
                  <PluralTranslate count={occurrenceCount}>
                    <Singular>Are you sure you want to cancel this booking?</Singular>
                    <Plural>
                      Are you sure you want to cancel this booking? This will cancel all{' '}
                      <Param name="count" value={occurrenceCount} wrapper={<strong />} />{' '}
                      occurrences.
                    </Plural>
                  </PluralTranslate>
                </p>
                <p>
                  {occurrenceCount > 1 && (
                    <Translate>
                      Single occurrences can be cancelled via the timeline view.
                    </Translate>
                  )}
                </p>
              </Modal.Content>
              <Modal.Actions>
                <Button onClick={this.hideConfirm} content={Translate.string('Close')} />
                {occurrenceCount > 1 && (
                  <Button
                    icon="calendar outline"
                    onClick={() => {
                      this.hideConfirm();
                      this.showOccurrences();
                    }}
                    content={Translate.string('View Timeline')}
                  />
                )}
                <Button
                  onClick={() => {
                    this.changeState('cancel');
                    this.hideConfirm();
                  }}
                  content={PluralTranslate.string(
                    'Cancel booking',
                    'Cancel all occurrences',
                    occurrenceCount
                  )}
                  negative
                />
              </Modal.Actions>
            </Modal>
          </>
        )}
        {canReject && (
          <Popup trigger={rejectButton} position="bottom center" on="click">
            <FinalForm
              onSubmit={data => this.changeState('reject', {reason: data.reason})}
              render={renderRejectionForm}
              subscription={{
                hasValidationErrors: true,
                submitSucceeded: true,
                submitting: true,
                pristine: true,
              }}
            />
          </Popup>
        )}
        {showAccept && (
          <Button.Group size="small" color="green">
            <Button
              type="button"
              icon="check circle"
              onClick={() => this.changeState('approve')}
              loading={actionInProgress === 'approve' && bookingStateChangeInProgress}
              disabled={bookingStateChangeInProgress || acceptanceFormVisible}
              content={Translate.string('Accept booking')}
            />
            <Popup
              trigger={acceptWithMessage}
              position="bottom right"
              on="click"
              open={acceptanceFormVisible}
              onOpen={this.showAcceptanceForm}
              onClose={this.hideAcceptanceForm}
            >
              <FinalForm
                onSubmit={data => this.changeState('approve', data)}
                render={renderAcceptanceForm}
                subscription={{
                  hasValidationErrors: true,
                  submitSucceeded: true,
                  submitting: true,
                  pristine: true,
                }}
              />
            </Popup>
          </Button.Group>
        )}
      </Modal.Actions>
    );
  };

  render() {
    const {occurrencesVisible} = this.state;
    const {
      onClose,
      editButton,
      bookingStateChangeInProgress,
      booking: {
        id,
        startDt,
        endDt,
        occurrences,
        dateRange,
        repetition,
        room,
        bookedForUser,
        bookingReason,
        editLogs,
        createdDt,
        createdByUser,
        isCancelled,
        isRejected,
        canDelete,
        canCancel,
        canReject,
        canAccept,
        canEdit,
        isAccepted,
        newBookingId,
        isLinkedToObject,
        link,
        externalDetailsURL,
      },
    } = this.props;
    const dates = {startDate: startDt, endDate: endDt};
    const times = {
      startTime: moment(startDt).format('HH:mm'),
      endTime: moment(endDt).format('HH:mm'),
    };
    const recurrence = getRecurrenceInfo(repetition);
    const showAccept = canAccept && !isAccepted;
    const showActionButtons = !isCancelled && !isRejected && (canCancel || canReject || showAccept);
    const activeBookings = _.omitBy(occurrences.bookings, value => _.isEmpty(value));
    const occurrenceCount = Object.keys(activeBookings).length;

    return (
      <>
        <Modal onClose={() => onClose()} size="large" closeIcon open>
          <Modal.Header styleName="booking-modal-header">
            <span styleName="header-text">
              <Translate>Booking Details</Translate>
            </span>
            <span styleName="booking-status">{this.renderBookingStatus()}</span>
            <ClipboardButton
              text={externalDetailsURL}
              successText={Translate.string('Booking link copied')}
            />
            <span>
              <Responsive.Tablet andLarger>
                {canEdit && editButton({disabled: bookingStateChangeInProgress})}
              </Responsive.Tablet>
              {canDelete && this.renderDeleteButton()}
            </span>
          </Modal.Header>
          <Modal.Content>
            <Grid stackable columns={2}>
              <Grid.Column>
                <RoomBasicDetails room={room} />
                <RoomKeyLocation room={room} />
                <TimeInformation
                  recurrence={recurrence}
                  dates={dates}
                  timeSlot={times}
                  onClickOccurrences={this.showOccurrences}
                  occurrenceCount={occurrenceCount}
                />
              </Grid.Column>
              <Grid.Column>
                <>
                  {bookedForUser && this.renderBookedFor(bookedForUser)}
                  {this.renderReason(bookingReason)}
                  {isLinkedToObject && (
                    <LazyBookingObjectLink type={_.camelCase(link.type)} id={link.id} />
                  )}
                  {this.renderBookingHistory(editLogs, createdDt, createdByUser)}
                  {this.renderMessageAfterSplitting(newBookingId)}
                </>
              </Grid.Column>
            </Grid>
          </Modal.Content>
          {showActionButtons &&
            this.renderActionButtons(canCancel, canReject, showAccept, occurrenceCount, isAccepted)}
        </Modal>
        <Modal open={occurrencesVisible} onClose={this.hideOccurrences} size="large" closeIcon>
          <Modal.Header className="legend-header">
            <Translate>Occurrences</Translate>
            <Popup
              trigger={<Icon name="info circle" className="legend-info-icon" />}
              content={<TimelineLegend labels={this.getLegendLabels(occurrences)} compact />}
            />
          </Modal.Header>
          <Modal.Content>{this.renderTimeline(occurrences, dateRange)}</Modal.Content>
        </Modal>
        {this.renderCancelOccurrence(occurrences.bookings, id)}
        {this.renderPreBookingWarning()}
      </>
    );
  }
}

export default connect(
  state => ({
    bookingStateChangeInProgress: bookingsSelectors.isBookingChangeInProgress(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        changeBookingState: bookingsActions.changeBookingState,
        changeBookingOccurrenceState: bookingsActions.changeBookingOccurrenceState,
        deleteBooking: bookingsActions.deleteBooking,
        openBookingDetails: bookingId => openModal('booking-details', bookingId, null, true),
        fetchBookingDetails: bookingsActions.fetchBookingDetails,
      },
      dispatch
    ),
  })
)(BookingDetails);
