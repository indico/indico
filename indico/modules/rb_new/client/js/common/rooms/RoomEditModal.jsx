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
import {Button, Form, Grid, Header, Modal} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './RoomEditModal.module.scss';


class RoomEditModal extends React.Component {
    static propTypes = {
        onClose: PropTypes.func.isRequired
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    renderModalContent = (fprops) => {
        const formProps = {onSubmit: fprops.onSubmit};
        return (
            <>
                <Modal.Header>
                    <Translate>Edit Room Details</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Form id="room-form" {...formProps}>
                        <Grid columns={3}>
                            <Grid.Column styleName="room-edit">
                                <Header>
                                    <Translate>Contact</Translate>
                                </Header>
                                <Field name="owner"
                                       component={ReduxFormField}
                                       label={Translate.string('Owner')}
                                       as="input" />
                                <Field name="key"
                                       component={ReduxFormField}
                                       label={Translate.string('Where is the key?')}
                                       as="input" />
                                <Field name="telephone"
                                       component={ReduxFormField}
                                       label={Translate.string('Telephone')}
                                       as="input" />
                                <Header>
                                    <Translate>Information</Translate>
                                </Header>
                                <Field name="capacity"
                                       component={ReduxFormField}

                                       label={Translate.string('Capacity (seats)')}
                                       as="input" />
                                <Field name="Division"
                                       component={ReduxFormField}
                                       label={Translate.string('Division')}
                                       as="input" />
                            </Grid.Column>
                            <Grid.Column>
                                <Header>
                                    <Translate>Location</Translate>
                                </Header>
                                <Field name="name"
                                       component={ReduxFormField}
                                       as="input"
                                       label={Translate.string('Name')} />
                                <Field name="site"
                                       component={ReduxFormField}
                                       label={Translate.string('Site')}
                                       as="input" />
                                <Form.Group widths="equal">
                                    <Field name="building"
                                           component={ReduxFormField}
                                           label={Translate.string('Building')}
                                           as="input" />
                                    <Field name="floor"
                                           component={ReduxFormField}
                                           label={Translate.string('Floor')}
                                           as="input" />
                                    <Field name="number"
                                           component={ReduxFormField}
                                           label={Translate.string('Number')}
                                           as="input" />
                                </Form.Group>
                                <Form.Group widths="equal">
                                    <Field name="longitude"
                                           component={ReduxFormField}
                                           label={Translate.string('Longitude')}
                                           as="input" />
                                    <Field name="latitude"
                                           component={ReduxFormField}
                                           label={Translate.string('Latitude')}
                                           as="input" />
                                </Form.Group>
                                <Field name="surface"
                                       component={ReduxFormField}
                                       label={Translate.string('Surface Area (m2)')}
                                       as="input" />
                                <Field name="maxAdvanceTime"
                                       component={ReduxFormField}
                                       label={Translate.string('Maximum advance time for bookings (days)')}
                                       as="input" />
                            </Grid.Column>
                            <Grid.Column>
                                <Header>
                                    <Translate>Options</Translate>
                                </Header>
                                <Field name="active"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Active')}
                                       as={Form.Checkbox} />
                                <Field name="public"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Public')}
                                       as={Form.Checkbox} />
                                <Field name="confirmations"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Confirmations')}
                                       as={Form.Checkbox} />
                                <Field name="reminders"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Reminders Enabled')}
                                       as={Form.Checkbox} />
                                <Field name="dayReminder"
                                       component={ReduxFormField}
                                       label={Translate.string('Send Booking reminders X days before (single/day)')}
                                       as="input" />
                                <Field name="weekReminder"
                                       component={ReduxFormField}
                                       label={Translate.string('Send Booking reminders X days before (weekly)')}
                                       as="input" />
                                <Field name="monthReminder"
                                       component={ReduxFormField}
                                       label={Translate.string('Send Booking reminders X days before (monthly)')}
                                       as="input" />
                            </Grid.Column>

                        </Grid>
                    </Form>
                </Modal.Content>
                <Modal.Actions>
                    <Button type="submit"
                            form="room-form"
                            primary>
                        <Translate>Save</Translate>
                    </Button>
                </Modal.Actions>
            </>
        );
    };

    render() {
        const name = 'test_name';
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <FinalForm render={this.renderModalContent}
                           onSubmit={() => null}
                           initialValues={{name}} />
            </Modal>
        );
    }
}

export default RoomEditModal;
