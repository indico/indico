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
import {Button, Checkbox, Form, Grid, Header, Modal} from 'semantic-ui-react';
import fetchRoomURL from 'indico-url:rooms_new.room';
import {Form as FinalForm, Field} from 'react-final-form';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {ReduxCheckboxField, ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './RoomEditModal.module.scss';


const contactDetails = [
    {name: 'ownerName',
     label: Translate.string('Owner')},
    {name: 'keyLocation',
     label: Translate.string('Where is the key?')},
    {name: 'telephone',
     label: Translate.string('Telephone')}];

const informationDetails = [
    {name: 'capacity',
     label: Translate.string('Capacity(seats)')},
    {name: 'division',
     label: Translate.string('Division')}];

const locationDetails = [
    {name: 'name',
     label: Translate.string('Name')},
    {name: 'site',
     label: Translate.string('Site')}];

const roomDetails = [
    {name: 'building',
     label: Translate.string('Building')},
    {name: 'floor',
     label: Translate.string('Floor')},
    {name: 'number',
     label: Translate.string('Number')}];

class RoomEditModal extends React.Component {
    static propTypes = {
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,

    };

    state = {
        room: {}
    };

    componentDidMount() {
        this.fetchDetailedRoom();
    }


    async fetchDetailedRoom() {
        const {roomId} = this.props;
        let response;
        try {
            response = await indicoAxios.get(fetchRoomURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        this.setState({room: camelizeKeys(response.data)});
    }

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
                                {contactDetails.map(contactDetail => (
                                    <Field key={contactDetail.name}
                                           name={contactDetail.name}
                                           component={ReduxFormField}
                                           label={contactDetail.label}
                                           as="input" />
                                ))}
                                <Header>
                                    <Translate>Information</Translate>
                                </Header>
                                <Form.Group widths="equal">
                                    {informationDetails.map(informationDetail => (
                                        <Field key={informationDetail.name}
                                               name={informationDetail.name}
                                               component={ReduxFormField}
                                               label={informationDetail.label}
                                               as="input" />
                                    ))}
                                </Form.Group>
                            </Grid.Column>
                            <Grid.Column>
                                <Header>
                                    <Translate>Location</Translate>
                                </Header>
                                {locationDetails.map(locationDetail => (
                                    <Field key={locationDetail.name}
                                           name={locationDetail.name}
                                           component={ReduxFormField}
                                           label={locationDetail.label}
                                           as="input" />))}
                                <Form.Group widths="equal">
                                    {roomDetails.map(roomDetail => (
                                        <Field key={roomDetail.name}
                                               name={roomDetail.name}
                                               component={ReduxFormField}
                                               label={roomDetail.label}
                                               as="input" />))}
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
                                <Field name="surfaceArea"
                                       component={ReduxFormField}
                                       label={Translate.string('Surface Area (m2)')}
                                       as="input" />
                                <Field name="maxAdvanceDays"
                                       component={ReduxFormField}
                                       label={Translate.string('Maximum advance time for bookings (days)')}
                                       as="input" />
                            </Grid.Column>
                            <Grid.Column>
                                <Header>
                                    <Translate>Options</Translate>
                                </Header>
                                <Field name="isActive"
                                       component={ReduxCheckboxField}
                                       componentLabel={Translate.string('Active')}
                                       checkBoxInput
                                       as={Checkbox} />
                                <Field name="isPublic"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Public')}
                                       as={Checkbox} />
                                <Field name="isAutoConfirm"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Confirmations')}
                                       as={Checkbox} />
                                <Field name="reminders"
                                       component={ReduxFormField}
                                       componentLabel={Translate.string('Reminders Enabled')}
                                       as={Checkbox} />
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
        const {room} = this.state;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <FinalForm render={this.renderModalContent}
                           onSubmit={() => null}
                           initialValues={room} />
            </Modal>
        );
    }
}

export default connect(
    null, null
)(RoomEditModal);
