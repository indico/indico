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
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Form as FinalForm, Field} from 'react-final-form';
import {Button, Icon, Confirm, Dropdown, Form, Portal, TextArea} from 'semantic-ui-react';

import {serializeDate} from 'indico/utils/date';
import {ReduxFormField, formatters, validators as v} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';
import * as bookingsActions from './actions';

import './OccurrenceActionsDropdown.module.scss';


class OccurrenceActionsDropdown extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        date: PropTypes.object.isRequired,
        actions: PropTypes.exact({
            changeBookingOccurrenceState: PropTypes.func.isRequired,
            fetchBookingDetails: PropTypes.func.isRequired
        }).isRequired,
    };

    constructor(props) {
        super(props);
        this.dropdownIconRef = React.createRef();
    }

    state = {
        activeConfirmation: null,
        dropdownOpen: false,
        top: 0,
        left: 0,
    };


    hideConfirm = () => {
        this.setState({activeConfirmation: null});
    };

    showConfirm = (type) => {
        this.setState({activeConfirmation: type});
    };

    changeOccurrenceState = (action, data = {}) => {
        const {
            date,
            booking: {id},
            actions: {changeBookingOccurrenceState, fetchBookingDetails}
        } = this.props;
        const serializedDate = serializeDate(date);
        changeBookingOccurrenceState(id, serializedDate, action, data).then(() => {
            fetchBookingDetails(id);
        });
    };

    findPositioning = () => {
        const positioning = this.dropdownIconRef.current.getBoundingClientRect();
        return {
            top: positioning.bottom - (positioning.height / 2),
            left: positioning.right,
        };
    };

    handleButtonClick = () => {
        const {top, left} = this.findPositioning();
        this.setState({
            dropdownOpen: true,
            top,
            left
        });
    };

    renderRejectionForm = ({handleSubmit, hasValidationErrors, submitSucceeded, submitting, pristine}) => {
        const {date} = this.props;
        const serializedDate = serializeDate(date, 'L');
        return (
            <Form styleName="rejection-form" onSubmit={handleSubmit}>
                <div styleName="form-description">
                    <Translate>
                        Are you sure you want to reject this occurrence (<Param name="date" value={serializedDate} />)?
                    </Translate>
                </div>
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
    };

    render() {
        const {activeConfirmation, dropdownOpen, top, left} = this.state;
        const {booking: {canCancel, canReject}, date} = this.props;
        const serializedDate = serializeDate(date, 'L');
        const rejectionForm = (
            <FinalForm onSubmit={(data) => this.changeOccurrenceState('reject', data)}
                       render={this.renderRejectionForm} />
        );

        if (!canCancel && !canReject) {
            return null;
        }

        const styleName = (dropdownOpen ? 'dropdown-button visible' : 'dropdown-button');
        return (
            <div styleName="actions-dropdown">
                <Portal closeOnTriggerClick
                        openOnTriggerClick
                        onOpen={this.handleButtonClick}
                        onClose={() => this.setState({dropdownOpen: false})}
                        trigger={
                            <Button styleName={styleName} onClick={this.handleButtonClick}>
                                <Button.Content>
                                    <div ref={this.dropdownIconRef}>
                                        <Icon name="ellipsis horizontal" size="big" />
                                    </div>
                                </Button.Content>
                            </Button>
                        }>
                    <Dropdown icon={null}
                              open
                              style={{left: `${left}px`, position: 'fixed', top: `${top}px`, zIndex: 1000}}>
                        <Dropdown.Menu direction="left">
                            {canCancel && (
                                <Dropdown.Item icon="times"
                                               text={Translate.string('Cancel occurrence')}
                                               onClick={() => this.showConfirm('cancel')} />
                            )}
                            {canReject && (
                                <Dropdown.Item icon="times circle"
                                               text={Translate.string('Reject occurrence')}
                                               onClick={() => this.showConfirm('reject')} />
                            )}
                        </Dropdown.Menu>
                    </Dropdown>
                </Portal>
                <Confirm header={Translate.string('Confirm cancellation')}
                         content={
                             Translate.string(
                                 'Are you sure you want to cancel this occurrence ({serializedDate})?',
                                 {serializedDate}
                             )
                         }
                         confirmButton={<Button content={Translate.string('Cancel occurrence')} negative />}
                         cancelButton={Translate.string('Close')}
                         open={activeConfirmation === 'cancel'}
                         onCancel={this.hideConfirm}
                         onConfirm={() => {
                             this.changeOccurrenceState('cancel');
                             this.hideConfirm();
                         }} />
                <Confirm header={Translate.string('Confirm rejection')}
                         content={rejectionForm}
                         confirmButton={null}
                         cancelButton={Translate.string('Close')}
                         open={activeConfirmation === 'reject'}
                         onCancel={this.hideConfirm} />
            </div>
        );
    }
}

export default connect(
    null,
    (dispatch) => ({
        actions: bindActionCreators({
            changeBookingOccurrenceState: bookingsActions.changeBookingOccurrenceState,
            fetchBookingDetails: bookingsActions.fetchBookingDetails
        }, dispatch)
    }),
)(OccurrenceActionsDropdown);
