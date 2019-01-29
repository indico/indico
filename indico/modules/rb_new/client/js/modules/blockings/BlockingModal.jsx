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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Confirm, Form, Grid, Message, Icon, Modal, Popup, TextArea} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {Param, Translate} from 'indico/react/i18n';
import {ReduxFormField, formatters, validators as v} from 'indico/react/forms';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import DatePeriodField from 'indico/react/components/DatePeriodField';
import RoomSelector from '../../components/RoomSelector';
import {selectors as userSelectors} from '../../common/user';
import * as blockingsActions from './actions';

import './BlockingModal.module.scss';


function validate({dates, reason, rooms}) {
    const errors = {};
    if (!dates) {
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
        favoriteUsers: PropTypes.array.isRequired,
        mode: PropTypes.oneOf(['view', 'edit', 'create']),
        blocking: PropTypes.shape({
            id: PropTypes.number,
            blockedRooms: PropTypes.array,
            allowed: PropTypes.array,
            startDate: PropTypes.string,
            endDate: PropTypes.string,
            reason: PropTypes.string,
            createdBy: PropTypes.string
        }),
        actions: PropTypes.exact({
            createBlocking: PropTypes.func.isRequired,
            updateBlocking: PropTypes.func.isRequired,
            acceptBlocking: PropTypes.func.isRequired,
            rejectBlocking: PropTypes.func.isRequired,
            deleteBlocking: PropTypes.func.isRequired,
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
            reason: ''
        }
    };

    constructor(props) {
        super(props);

        const {mode} = this.props;
        this.state = {
            deletionConfirmOpen: false,
            mode,
        };
    }

    handleSubmit = async (formData) => {
        const {actions: {createBlocking, updateBlocking}, blocking: {id}} = this.props;
        const {mode} = this.state;
        let rv;

        if (mode === 'create') {
            rv = await createBlocking(formData);
        } else if (mode === 'edit') {
            rv = await updateBlocking(id, formData);
        }

        if (rv.error) {
            return rv.error;
        }
    };

    renderPrincipalSearchField = (props) => {
        const {favoriteUsers} = this.props;
        return (
            <ReduxFormField {...props}
                            favoriteUsers={favoriteUsers}
                            as={PrincipalSearchField}
                            label={Translate.string('Allowed users / groups')}
                            multiple
                            withGroups />
        );
    };

    renderBlockingPeriodField = ({input, ...props}) => {
        const {mode} = this.state;
        return (
            <ReduxFormField {...props}
                            input={input}
                            as={DatePeriodField}
                            label={Translate.string('Period')}
                            required={mode === 'create'} />
        );
    };

    renderRoomState = (room) => {
        const {blocking: {canEdit, id}, actions: {acceptBlocking, rejectBlocking}} = this.props;
        const {state} = room;
        const {mode} = this.state;
        if (!room.state) {
            return null;
        }

        const {rejectionReason, rejectedBy} = room;
        const stateIconProps = {
            accepted: {name: 'check circle', color: 'green'},
            rejected: {name: 'dont', color: 'red'},
            pending: {name: 'question circle', color: 'orange'}
        }[state];

        let popupContent;
        if (state === 'accepted') {
            popupContent = Translate.string('Blocking has been accepted');
        } else if (state === 'pending') {
            popupContent = Translate.string('Pending blocking');
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

        const renderRejectionForm = ({handleSubmit, hasValidationErrors, submitSucceeded, submitting, pristine}) => (
            <Form styleName="rejection-form" onSubmit={handleSubmit}>
                <Field name="reason"
                       component={ReduxFormField}
                       as={TextArea}
                       format={formatters.trim}
                       placeholder={Translate.string('Provide the rejection reason')}
                       rows={2}
                       validate={v.required}
                       disabled={submitting}
                       required
                       formatOnBlur />
                <Button type="submit"
                        disabled={submitting || pristine || hasValidationErrors || submitSucceeded}
                        loading={submitting}
                        floated="right"
                        primary>
                    <Translate>Reject</Translate>
                </Button>
            </Form>
        );

        return (
            <div styleName="blocking-actions">
                {mode === 'view' && state === 'pending' && canEdit && (
                    <>
                        <Popup trigger={<Icon name="check" color="green" size="large" styleName="action"
                                              onClick={() => acceptBlocking(id, room.id)} />}
                               position="bottom center"
                               content={Translate.string('Accept blocking')}
                               flowing />
                        <Popup trigger={<Icon name="dont" color="red" size="large" styleName="action" />}
                               position="bottom center"
                               on="click"
                               flowing>
                            <FinalForm onSubmit={({reason}) => rejectBlocking(id, room.id, reason)}
                                       render={renderRejectionForm} />
                        </Popup>
                    </>
                )}
                <Popup trigger={<Icon size="large" {...stateIconProps} />}
                       position="right center"
                       content={popupContent}
                       flowing />
            </div>
        );
    };

    renderRoomSearchField = ({input, ...props}) => {
        const {mode} = this.state;
        let label;

        if (mode === 'create') {
            label = Translate.string('Rooms to block');
        } else {
            label = Translate.string('Blocked rooms');
        }

        return (
            <ReduxFormField {...props}
                            input={input}
                            as={RoomSelector}
                            label={label}
                            required={mode !== 'view'}
                            renderRoomActions={this.renderRoomState} />
        );
    };

    renderSubmitButton = ({hasValidationErrors, pristine, submitting, submitSucceeded}) => {
        const {mode} = this.state;
        return (
            <Button type="submit"
                    form="blocking-form"
                    disabled={hasValidationErrors || pristine || submitSucceeded}
                    loading={submitting}
                    primary>
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
            return <Translate>Update blocking</Translate>;
        } else {
            return <Translate>Block selected spaces</Translate>;
        }
    };

    hasAllowedFieldChanged = (prevValue, nextValue) => {
        if (!prevValue || prevValue.length !== nextValue.length) {
            return true;
        }

        prevValue = _.sortBy(prevValue, 'id');
        nextValue = _.sortBy(nextValue, 'id');
        return !_.every(nextValue, (val, index) => val.id === prevValue[index].id);
    };

    deleteBlocking = () => {
        const {blocking: {id}, actions: {deleteBlocking}, onClose} = this.props;
        deleteBlocking(id);
        onClose();
    };

    renderModalContent = (fprops) => {
        const {onClose, blocking} = this.props;
        const {submitting, submitSucceeded} = fprops;
        const {mode, deletionConfirmOpen} = this.state;
        const formProps = mode === 'view' ? {} : {onSubmit: fprops.handleSubmit, success: submitSucceeded};
        const canEdit = !!blocking.id && blocking.canEdit;
        const canDelete = !!blocking.id && blocking.canDelete;

        return (
            <>
                <Modal.Header styleName="blocking-modal-header">
                    {this.renderHeaderText()}
                    <span>
                        {canEdit && (
                            <Button icon="pencil"
                                    primary={mode === 'edit'}
                                    onClick={() => {
                                        if (mode === 'edit') {
                                            fprops.form.reset();
                                            this.setState({mode: 'view'});
                                        } else {
                                            this.setState({mode: 'edit'});
                                        }
                                    }}
                                    circular />
                        )}
                        {canDelete && (
                            <>
                                <Button icon="trash" color="red"
                                        onClick={() => this.setState({deletionConfirmOpen: true})}
                                        circular />
                                <Confirm header={Translate.string('Confirm deletion')}
                                         content={Translate.string('Are you sure you want to delete this blocking?')}
                                         confirmButton={<Button content={Translate.string('Delete')} negative />}
                                         cancelButton={Translate.string('Cancel')}
                                         open={deletionConfirmOpen}
                                         onConfirm={this.deleteBlocking}
                                         onCancel={() => this.setState({deletionConfirmOpen: false})} />
                            </>
                        )}
                    </span>
                </Modal.Header>
                <Modal.Content>
                    <Form id="blocking-form" {...formProps}>
                        <Grid>
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
                                            When blocking rooms nobody but you, the rooms' managers and those
                                            users/groups you specify in the "Allowed users/groups" list will be able
                                            to create bookings for the specified rooms in the given timeframe.
                                            You can also block rooms you do not own - however, those blockings have to
                                            be approved by the owners of those rooms.
                                        </Translate>
                                    </Message.Content>
                                </Message>
                                <Message negative icon>
                                    <Icon name="warning sign" />
                                    <Message.Content>
                                        <Translate>
                                            Please take into account that rooms blockings should only be used for short
                                            term events and never for long-lasting periods. If you wish to somehow
                                            mark a room as unusable, please ask its owner to set it as such.
                                        </Translate>
                                    </Message.Content>
                                </Message>
                                <Field name="dates"
                                       render={this.renderBlockingPeriodField}
                                       disabled={mode !== 'create' || submitting || submitSucceeded}
                                       allowNull />
                                <Field name="reason"
                                       format={formatters.trim}
                                       render={(fieldProps) => {
                                           const props = {};
                                           if (mode === 'edit') {
                                               props.defaultValue = blocking.reason;
                                               props.value = undefined;
                                           } else if (mode === 'view') {
                                               props.value = blocking.reason;
                                           }

                                           return (
                                               <ReduxFormField {...fieldProps}
                                                               {...props}
                                                               as={Form.TextArea}
                                                               label={Translate.string('Reason')}
                                                               placeholder={Translate.string('Provide reason for blocking')}
                                                               disabled={mode === 'view' || submitting || submitSucceeded}
                                                               required={mode !== 'view'} />
                                           );
                                       }}
                                       formatOnBlur />
                            </Grid.Column>
                            <Grid.Column width={8}>
                                <Field name="allowed"
                                       isEqual={(a, b) => !this.hasAllowedFieldChanged(a, b)}
                                       render={this.renderPrincipalSearchField}
                                       disabled={mode === 'view' || submitting || submitSucceeded} />
                                <Field name="rooms"
                                       isEqual={_.isEqual}
                                       render={this.renderRoomSearchField}
                                       disabled={mode === 'view' || submitting || submitSucceeded} />
                                {blocking.canEdit && blocking.blockedRooms.length !== 0 && (
                                    <Message icon info>
                                        <Icon name="info" />
                                        <Translate>
                                            You can accept and reject blockings for the rooms on the list
                                            by using the action buttons on the right side of the room name.
                                        </Translate>
                                    </Message>
                                )}
                                <Message success>
                                    {mode === 'edit' ? (
                                        <Translate>The blocking has been successfully updated.</Translate>
                                    ) : (
                                        <Translate>The blocking has been successfully created.</Translate>
                                    )}
                                </Message>
                            </Grid.Column>
                        </Grid>
                    </Form>
                </Modal.Content>
                <Modal.Actions>
                    {mode !== 'view' && this.renderSubmitButton(fprops)}
                    <Button type="button" onClick={onClose}>
                        <Translate>
                            Close
                        </Translate>
                    </Button>
                </Modal.Actions>
            </>
        );
    };

    render() {
        const {onClose, blocking: {blockedRooms, allowed, startDate, endDate, reason}} = this.props;
        const {mode} = this.state;
        const props = mode === 'view' ? {onSubmit() {}} : {validate, onSubmit: this.handleSubmit};
        const dates = mode !== 'create' ? {startDate, endDate} : null;
        const rooms = blockedRooms.map(({room, state, rejectionReason, rejectedBy}) => ({
            ...room,
            state,
            rejectionReason,
            rejectedBy
        }));

        return (
            <Modal open onClose={onClose} size="large" closeIcon>
                <FinalForm {...props}
                           render={this.renderModalContent}
                           initialValues={{rooms, dates, allowed: allowed || [], reason}}
                           subscription={{
                               submitting: true,
                               hasValidationErrors: true,
                               pristine: true,
                               submitSucceeded: true
                           }} />
            </Modal>
        );
    }
}

export default connect(
    state => ({
        favoriteUsers: userSelectors.getFavoriteUsers(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            createBlocking: blockingsActions.createBlocking,
            updateBlocking: blockingsActions.updateBlocking,
            acceptBlocking: blockingsActions.acceptBlocking,
            rejectBlocking: blockingsActions.rejectBlocking,
            deleteBlocking: blockingsActions.deleteBlocking,
        }, dispatch),
    })
)(BlockingModal);
