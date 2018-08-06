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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Button, Divider, Form, Grid, Message, Icon, Modal} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import setFieldTouched from 'final-form-set-field-touched';
import createDecorator from 'final-form-calculate';
import {Translate} from 'indico/react/i18n';
import {ReduxFormField, formatters} from 'indico/react/forms';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import DatePeriodField from 'indico/react/components/DatePeriodField';
import RoomSelector from '../RoomSelector';
import {createBlocking} from '../../actions';


function validate({period, reason, rooms}) {
    const errors = {};
    if (period === undefined || !period.length) {
        errors.period = Translate.string('Please choose a valid period!');
    }
    if (!reason) {
        errors.reason = Translate.string('Please provide the reason for the blocking!');
    }
    if (rooms === undefined || !rooms.length) {
        errors.rooms = Translate.string('Please choose at least one room for this blocking!');
    }
    return errors;
}

const formDecorator = createDecorator({
    field: 'period',
    updates: (periodValue) => {
        return {
            start_date: periodValue[0],
            end_date: periodValue[1]
        };
    }
}, {
    field: 'rooms',
    updates: (rooms) => {
        return {
            room_ids: rooms.map((room) => room.id)
        };
    }
}, {
    field: 'allowed',
    updates: (allowed) => {
        return {
            allowed_principals: allowed.map((obj) => ({
                id: obj.id,
                is_group: obj.is_group
            }))
        };
    }
});


class BlockingModal extends React.Component {
    static propTypes = {
        open: PropTypes.bool.isRequired,
        onClose: PropTypes.func.isRequired,
        rooms: PropTypes.array,
        createBlocking: PropTypes.func.isRequired
    };

    static defaultProps = {
        rooms: []
    };

    createBlocking = async (formData) => {
        await this.props.createBlocking(formData); // eslint-disable-line react/destructuring-assignment
    };

    renderPrincipalSearchField = ({input, ...props}) => {
        return (
            <ReduxFormField input={input}
                            as={PrincipalSearchField}
                            label={Translate.string('Allowed users / groups')}
                            onChange={(user) => {
                                input.onChange(user);
                            }}
                            multiple
                            withGroups
                            {...props} />
        );
    };

    renderBlockingPeriodField = ({input, ...props}) => {
        return (
            <ReduxFormField input={input}
                            as={DatePeriodField}
                            label={Translate.string('Period')}
                            onChange={(dates) => {
                                input.onChange(dates);
                            }}
                            required
                            {...props} />
        );
    };

    renderRoomSearchField = ({input, ...props}) => {
        const {rooms} = this.props;
        return (
            <ReduxFormField input={input}
                            as={RoomSelector}
                            initialValue={rooms}
                            label={Translate.string('Rooms to block')}
                            onChange={(values) => {
                                input.onChange(values);
                            }}
                            required
                            {...props} />
        );
    };

    renderSubmitButton = ({hasValidationErrors, pristine, submitting, submitSucceeded}) => {
        return (
            <Button type="submit"
                    form="blocking-form"
                    disabled={hasValidationErrors || pristine || submitSucceeded}
                    loading={submitting}
                    primary>
                <Translate>Create a blocking</Translate>
            </Button>
        );
    };

    renderModalContent = (fprops) => {
        const {onClose} = this.props;
        const {form: {mutators}, submitSucceeded} = fprops;

        // set `touched` flag so in case of a validation error we properly
        // show the error label
        mutators.setFieldTouched('rooms', true);

        return (
            <>
                <Modal.Header>
                    <Translate>Create a blocking</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Form id="blocking-form" onSubmit={fprops.handleSubmit}>
                        <Grid>
                            <Grid.Column width={8}>
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
                                <Message color="red" icon>
                                    <Icon name="warning sign" />
                                    <Message.Content>
                                        <Translate>
                                            When blocking rooms nobody but you, the rooms' managers and those
                                            users/groups you specify in the "Allowed users/groups" list will be able to
                                            create bookings for the specified rooms in the given timeframe. You can
                                            also block rooms you do not own - however, those blockings have to be
                                            approved by the owners of those rooms.
                                        </Translate>
                                    </Message.Content>
                                </Message>
                                <Divider hidden section />
                                <Field name="rooms"
                                       component={this.renderRoomSearchField} />
                            </Grid.Column>
                            <Grid.Column width={8}>
                                <Field name="allowed"
                                       component={this.renderPrincipalSearchField} />
                                <Field name="period"
                                       component={this.renderBlockingPeriodField} />
                                <Field name="reason"
                                       label={Translate.string('Reason')}
                                       component={ReduxFormField}
                                       as={Form.TextArea}
                                       format={formatters.trim}
                                       placeholder={Translate.string('Reason for blocking')}
                                       formatOnBlur
                                       required />
                                {submitSucceeded && (
                                    <Message positive>
                                        <Translate>
                                            The blocking has been successfully created.
                                        </Translate>
                                    </Message>
                                )}
                            </Grid.Column>
                        </Grid>
                    </Form>
                </Modal.Content>
                <Modal.Actions>
                    {this.renderSubmitButton(fprops)}
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
        const {open, onClose} = this.props;
        return (
            <Modal open={open} onClose={onClose} size="large" closeIcon>
                <FinalForm onSubmit={this.createBlocking}
                           validate={validate}
                           render={this.renderModalContent}
                           mutators={{setFieldTouched}}
                           decorators={[formDecorator]} />
            </Modal>
        );
    }
}

const mapDispatchToProps = (dispatch) => ({
    createBlocking: (formData) => {
        return dispatch(createBlocking(formData));
    }
});

export default connect(
    null,
    mapDispatchToProps
)(BlockingModal);
