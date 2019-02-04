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

import ReactDom from 'react-dom';
import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Form as FinalForm, Field} from 'react-final-form';
import {Button, Confirm, Dropdown, Form, Portal, TextArea} from 'semantic-ui-react';

import {ReduxFormField, formatters, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import * as bookingsActions from './actions';

import './OccurrenceActionsDropdown.module.scss';


class OccurrenceActionsDropdown extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        date: PropTypes.string.isRequired,
        actions: PropTypes.exact({
            changeBookingOccurrenceState: PropTypes.func.isRequired,
            fetchBookingDetails: PropTypes.func.isRequired
        }).isRequired,
    };

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
        const {date} = this.props;
        const {booking: {id}, actions: {changeBookingOccurrenceState, fetchBookingDetails}} = this.props;
        changeBookingOccurrenceState(id, date, action, data).then(() => {
            fetchBookingDetails(id);
        });
    };

    findPositioning = () => {
        const positioning = ReactDom.findDOMNode(this).getBoundingClientRect();
        return {
            top: positioning.top,
            left: positioning.left
        };
    };

    onClickButton = () => {
        const {dropdownOpen} = this.state;
        const {top, left} = this.findPositioning();
        if (dropdownOpen) {
            this.setState({
                dropdownOpen: false,
                top,
                left
            });
        } else {
            this.setState({
                dropdownOpen: true,
                top,
                left
            });
        }
    };

    renderRejectionForm = ({handleSubmit, hasValidationErrors, submitSucceeded, submitting, pristine}) => {
        return (
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
                <Button type="negative"
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
        const rejectionForm = (
            <FinalForm onSubmit={(data) => this.changeOccurrenceState('reject', data)}
                       render={this.renderRejectionForm} />
        );
        if (!canCancel && !canReject) {
            return (null);
        }
        return (
            <div styleName="actions-dropdown">
                <Button icon="ellipsis horizontal" onClick={this.onClickButton} />
                <Portal open={dropdownOpen} onClose={() => this.setState({dropdownOpen: false})}>
                    <Dropdown icon={null}
                              open
                              style={{left: `${left}px`, position: 'fixed', top: `${top}px`, zIndex: 1000}}>
                        <Dropdown.Menu direction="left">
                            {canCancel && (
                                <Dropdown.Item icon="times"
                                               text="Cancel occurrence"
                                               onClick={() => this.showConfirm('cancel')} />
                            )}
                            {canReject && (
                                <Dropdown.Item icon="times"
                                               text="Reject occurrence"
                                               onClick={() => this.showConfirm('reject')} />
                            )}
                        </Dropdown.Menu>
                    </Dropdown>
                </Portal>
                <Confirm header={Translate.string('Confirm cancellation')}
                         content={Translate.string(`Are you sure you want to cancel this occurrence (${date})?`)}
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
