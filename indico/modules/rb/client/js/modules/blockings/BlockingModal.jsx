// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Button, Confirm, Form, Grid, Message, Icon, Modal, Popup} from 'semantic-ui-react';

import {FinalDateRangePicker, FinalPrincipalList} from 'indico/react/components';
import {FinalTextArea} from 'indico/react/forms';
import {FavoritesProvider} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

import {selectors as userSelectors} from '../../common/user';
import FinalRoomSelector from '../../components/RoomSelector';

import * as blockingsActions from './actions';

import './BlockingModal.module.scss';

function validate({dates, reason, rooms}) {
  const errors = {};
  if (!dates || !Object.values(dates).every(x => x)) {
    errors.dates = Translate.string('Please choose a valid period.');
  }
  if (!reason) {
    errors.reason = Translate.string('Please provide the reason for the blocking.');
  }
  if (!rooms || !rooms.length) {
    errors.rooms = Translate.string('Please choose at least one room for this blocking.');
  }
  return errors;
}

class BlockingModal extends React.Component {
  static propTypes = {
    onClose: PropTypes.func.isRequired,
    managedRoomIds: PropTypes.object.isRequired,
    mode: PropTypes.oneOf(['view', 'edit', 'create']),
    blocking: PropTypes.shape({
      id: PropTypes.number,
      blockedRooms: PropTypes.array,
      allowed: PropTypes.array,
      startDate: PropTypes.string,
      endDate: PropTypes.string,
      reason: PropTypes.string,
      createdBy: PropTypes.string,
      canDelete: PropTypes.bool,
      canEdit: PropTypes.bool,
    }),
    actions: PropTypes.exact({
      createBlocking: PropTypes.func.isRequired,
      updateBlocking: PropTypes.func.isRequired,
      acceptBlocking: PropTypes.func.isRequired,
      rejectBlocking: PropTypes.func.isRequired,
      deleteBlocking: PropTypes.func.isRequired,
      openBlockingDetails: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    mode: 'view',
    blocking: {
      id: null,
      blockedRooms: [],
      allowed: [],
      startDate: null,
      endDate: null,
      reason: '',
    },
  };

  constructor(props) {
    super(props);

    const {mode} = this.props;
    this.state = {
      deletionConfirmOpen: false,
      newBlocking: null,
      mode,
    };
  }

  handleSubmit = async formData => {
    const {
      actions: {createBlocking, updateBlocking},
      blocking: {id},
    } = this.props;
    const {mode} = this.state;
    let rv;

    if (mode === 'create') {
      rv = await createBlocking(formData);
    } else if (mode === 'edit') {
      rv = await updateBlocking(id, formData);
    }

    if (rv.error) {
      return rv.error;
    } else {
      this.setState({newBlocking: rv.data});
    }
  };

  renderRoomState = room => {
    const {
      managedRoomIds,
      blocking: {id},
      actions: {acceptBlocking, rejectBlocking},
    } = this.props;
    const {state} = room;
    const {mode} = this.state;
    if (!room.state) {
      return null;
    }

    const {rejectionReason, rejectedBy} = room;
    const stateIconProps = {
      accepted: {name: 'check circle', color: 'green'},
      rejected: {name: 'dont', color: 'red'},
      pending: {name: 'question circle', color: 'orange'},
    }[state];

    let popupContent;
    if (state === 'accepted') {
      popupContent = Translate.string('Blocking has been accepted');
    } else if (state === 'pending') {
      popupContent = Translate.string('Pending approval by a room manager');
    } else {
      popupContent = (
        <>
          <Translate>
            Booking rejected by <Param name="rejectedBy" value={rejectedBy} wrapper={<strong />} />
          </Translate>
          <br />
          <Translate>
            Reason: <Param name="rejectionReason" value={rejectionReason} wrapper={<strong />} />
          </Translate>
        </>
      );
    }

    const renderRejectionForm = ({
      handleSubmit,
      hasValidationErrors,
      submitSucceeded,
      submitting,
      pristine,
    }) => (
      <Form styleName="rejection-form" onSubmit={handleSubmit}>
        <FinalTextArea
          name="reason"
          placeholder={Translate.string('Provide the rejection reason')}
          disabled={submitSucceeded}
          rows={2}
          required
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

    return (
      <div styleName="blocking-actions">
        {mode === 'view' && state === 'pending' && managedRoomIds.has(room.id) && (
          <>
            <Popup
              trigger={
                <Icon
                  name="check"
                  color="green"
                  size="large"
                  styleName="action"
                  onClick={() => acceptBlocking(id, room.id)}
                />
              }
              position="bottom center"
              content={Translate.string('Accept blocking')}
              flowing
            />
            <Popup
              trigger={<Icon name="dont" color="red" size="large" styleName="action" />}
              position="bottom center"
              on="click"
              flowing
            >
              <FinalForm
                onSubmit={({reason}) => rejectBlocking(id, room.id, reason)}
                render={renderRejectionForm}
              />
            </Popup>
          </>
        )}
        <Popup
          trigger={<Icon size="large" {...stateIconProps} />}
          position="right center"
          content={popupContent}
          flowing
        />
      </div>
    );
  };

  renderSubmitButton = ({hasValidationErrors, pristine, submitting, submitSucceeded}) => {
    const {mode} = this.state;
    return (
      <Button
        type="submit"
        form="blocking-form"
        disabled={submitting || hasValidationErrors || pristine || submitSucceeded}
        loading={submitting}
        primary
      >
        {mode === 'edit' ? (
          <Translate>Update blocking</Translate>
        ) : (
          <Translate>Block selected spaces</Translate>
        )}
      </Button>
    );
  };

  renderHeaderText = () => {
    const {mode} = this.state;
    if (mode === 'view') {
      return <Translate>Blocking details</Translate>;
    } else if (mode === 'edit') {
      return <Translate>Edit blocking</Translate>;
    } else {
      return <Translate>Block selected spaces</Translate>;
    }
  };

  deleteBlocking = () => {
    const {
      blocking: {id},
      actions: {deleteBlocking},
      onClose,
    } = this.props;
    deleteBlocking(id);
    onClose();
  };

  get hasManagedPendingRooms() {
    const {
      managedRoomIds,
      blocking: {blockedRooms},
    } = this.props;
    return blockedRooms.some(br => br.state === 'pending' && managedRoomIds.has(br.room.id));
  }

  renderModalContent = fprops => {
    const {
      onClose,
      blocking,
      actions: {openBlockingDetails},
    } = this.props;
    const {submitSucceeded} = fprops;
    const {mode, deletionConfirmOpen, newBlocking} = this.state;
    const formProps =
      mode === 'view' ? {} : {onSubmit: fprops.handleSubmit, success: submitSucceeded};
    const canEdit = !!blocking.id && blocking.canEdit;
    const canDelete = !!blocking.id && blocking.canDelete;
    const newBlockingLink = <a onClick={() => openBlockingDetails(newBlocking.id)} />;

    return (
      <>
        <Modal.Header styleName="blocking-modal-header">
          {this.renderHeaderText()}
          <span>
            {canEdit && (
              <Button
                icon="pencil"
                primary={mode === 'edit'}
                onClick={() => {
                  if (mode === 'edit') {
                    fprops.form.reset();
                    this.setState({mode: 'view'});
                  } else {
                    this.setState({mode: 'edit'});
                  }
                }}
                circular
              />
            )}
            {canDelete && (
              <>
                <Button
                  icon="trash"
                  color="red"
                  onClick={() => this.setState({deletionConfirmOpen: true})}
                  circular
                />
                <Confirm
                  header={Translate.string('Confirm deletion')}
                  content={Translate.string('Are you sure you want to delete this blocking?')}
                  confirmButton={<Button content={Translate.string('Delete')} negative />}
                  cancelButton={Translate.string('Cancel')}
                  open={deletionConfirmOpen}
                  onConfirm={this.deleteBlocking}
                  onCancel={() => this.setState({deletionConfirmOpen: false})}
                />
              </>
            )}
          </span>
        </Modal.Header>
        <Modal.Content>
          <Form id="blocking-form" {...formProps}>
            <Grid stackable>
              <Grid.Column width={8}>
                {mode !== 'create' && (
                  <Message icon info floating>
                    <Icon name="user" />
                    <Message.Content>
                      <Translate>
                        Blocking created by <Param name="createdBy" value={blocking.createdBy} />
                      </Translate>
                    </Message.Content>
                  </Message>
                )}
                <Message icon info>
                  <Icon name="lightbulb" />
                  <Message.Content>
                    <Translate>
                      When blocking rooms nobody but you, the rooms' managers and those users/groups
                      you specify in the "Allowed users/groups" list will be able to create bookings
                      for the specified rooms in the given timeframe. You can also block rooms you
                      do not own - however, those blockings have to be approved by the owners of
                      those rooms.
                    </Translate>
                  </Message.Content>
                </Message>
                <Message negative icon>
                  <Icon name="warning sign" />
                  <Message.Content>
                    <Translate>
                      Please take into account that rooms blockings should only be used for short
                      term events and never for long-lasting periods. If you wish to somehow mark a
                      room as unusable, please ask its owner to set it as such.
                    </Translate>
                  </Message.Content>
                </Message>
                <FinalDateRangePicker
                  name="dates"
                  label={Translate.string('Period')}
                  required={mode === 'create'}
                  readOnly={mode !== 'create'}
                  disabled={submitSucceeded}
                  min={serializeDate(moment())}
                  allowNull
                />
                <FinalTextArea
                  name="reason"
                  label={Translate.string('Reason')}
                  placeholder={Translate.string('Provide reason for blocking')}
                  readOnly={mode === 'view'}
                  disabled={submitSucceeded}
                  required={mode !== 'view'}
                />
              </Grid.Column>
              <Grid.Column width={8}>
                <FavoritesProvider>
                  {favoriteUsersController => (
                    <FinalPrincipalList
                      name="allowed"
                      withGroups
                      favoriteUsersController={favoriteUsersController}
                      label={Translate.string('Authorized users/groups')}
                      readOnly={mode === 'view'}
                      disabled={submitSucceeded}
                    />
                  )}
                </FavoritesProvider>
                <FinalRoomSelector
                  name="rooms"
                  label={
                    mode === 'create'
                      ? Translate.string('Rooms to block')
                      : Translate.string('Blocked rooms')
                  }
                  required={mode !== 'view'}
                  renderRoomActions={this.renderRoomState}
                  disabled={submitSucceeded}
                  readOnly={mode === 'view'}
                />
                {mode === 'view' && this.hasManagedPendingRooms && (
                  <Message icon info>
                    <Icon name="info" />
                    <Translate>
                      You can accept and reject blockings for your rooms on the list by using the
                      action buttons on the right side of the room name.
                    </Translate>
                  </Message>
                )}
                {mode === 'edit' ? (
                  <Message success>
                    <Translate>The blocking has been successfully updated.</Translate>
                  </Message>
                ) : (
                  <Message success>
                    <Message.Header>
                      <Translate>The blocking has been successfully created.</Translate>
                    </Message.Header>
                    <Translate>
                      You can consult your blocking{' '}
                      <Param name="link" wrapper={newBlockingLink}>
                        here
                      </Param>
                      .
                    </Translate>
                  </Message>
                )}
              </Grid.Column>
            </Grid>
          </Form>
        </Modal.Content>
        <Modal.Actions>
          {mode !== 'view' && this.renderSubmitButton(fprops)}
          <Button type="button" onClick={onClose}>
            <Translate>Close</Translate>
          </Button>
        </Modal.Actions>
      </>
    );
  };

  render() {
    const {
      onClose,
      blocking: {blockedRooms, allowed, startDate, endDate, reason},
    } = this.props;
    const {mode} = this.state;
    const props = mode === 'view' ? {onSubmit() {}} : {validate, onSubmit: this.handleSubmit};
    const dates = mode !== 'create' ? {startDate, endDate} : null;
    const rooms = blockedRooms.map(({room, state, rejectionReason, rejectedBy}) => ({
      ...room,
      state,
      rejectionReason,
      rejectedBy,
    }));

    return (
      <Modal open onClose={onClose} size="large" closeIcon>
        <FinalForm
          {...props}
          render={this.renderModalContent}
          initialValues={{rooms, dates, allowed: allowed || [], reason}}
          initialValuesEqual={_.isEqual}
          subscription={{
            submitting: true,
            hasValidationErrors: true,
            pristine: true,
            submitSucceeded: true,
          }}
        />
      </Modal>
    );
  }
}

export default connect(
  state => ({
    managedRoomIds: new Set(userSelectors.getManagedRoomIds(state)),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        createBlocking: blockingsActions.createBlocking,
        updateBlocking: blockingsActions.updateBlocking,
        acceptBlocking: blockingsActions.acceptBlocking,
        rejectBlocking: blockingsActions.rejectBlocking,
        deleteBlocking: blockingsActions.deleteBlocking,
        openBlockingDetails: blockingId => {
          return blockingsActions.openBlockingDetails(blockingId, '/blockings');
        },
      },
      dispatch
    ),
  })
)(BlockingModal);
