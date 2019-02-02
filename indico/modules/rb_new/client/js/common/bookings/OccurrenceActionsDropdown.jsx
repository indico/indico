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
import {Button, Confirm, Dropdown, Form, Popup, TextArea} from 'semantic-ui-react';

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
        dropdownUpward: false,
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

    findHeightRatio = () => {
        const windowHeight = window.innerHeight;
        const elementHeight = ReactDom.findDOMNode(this).getBoundingClientRect().top;
        return elementHeight / windowHeight;
    };

    onClickButton = () => {
        const {dropdownUpward, dropdownOpen} = this.state;
        if (dropdownOpen) {
            this.setState({dropdownOpen: false});
        } else {
            const ratio = this.findHeightRatio();
            const setUpward = (ratio > 0.75 && !dropdownUpward);
            const setDownward = (ratio < 0.75 && dropdownUpward);
            if (setUpward) {
                this.setState({
                    dropdownOpen: true,
                    dropdownUpward: true,
                });
            } else if (setDownward) {
                this.setState({
                    dropdownOpen: true,
                    dropdownUpward: false,
                });
            } else {
                this.setState({dropdownOpen: true});
            }
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
        const {activeConfirmation, dropdownUpward, dropdownOpen} = this.state;
        const {date} = this.props;
        const rejectButton = (<Dropdown.Item icon="times" text="Reject occurrence" />);
        return (
            <div styleName="actions-dropdown">
                <Button icon="ellipsis horizontal" onClick={this.onClickButton} />
                <Dropdown upward={dropdownUpward} open={dropdownOpen}>
                    <Dropdown.Menu direction="left">
                        <Dropdown.Item icon="times"
                                       text="Cancel occurrence"
                                       onClick={() => this.showConfirm('cancel')} />
                        <Popup trigger={rejectButton}
                               position="bottom center"
                               on="click">
                            <FinalForm onSubmit={(data) => this.changeOccurrenceState('reject', data)}
                                       render={this.renderRejectionForm} />
                        </Popup>
                    </Dropdown.Menu>
                </Dropdown>
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
