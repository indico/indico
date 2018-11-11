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
import {Button, Checkbox, Dimmer, Form, Grid, Header, Loader, Modal} from 'semantic-ui-react';
import fetchRoomURL from 'indico-url:rooms_new.room';
import {Form as FinalForm, Field} from 'react-final-form';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {ReduxCheckboxField, ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import * as roomActions from './actions';

import './RoomEditModal.module.scss';

function validate({}) {
};

class RoomEditModal extends React.Component {
    static propTypes = {
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,

    };

    state = {
        room: null
    };

    componentDidMount() {
        this.fetchDetailedRoom();
    };

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

    handleSubmit = async (formData) => {
        const {actions: {updateRoom}, room: {id}} = this.props;
        let rv = await updateRoom(id, formData);
        if(rv.error){
            return rv.error;
        }
    };

    renderHeader = (title) => (
        <Header key={title}>
            <Translate>{title}</Translate>
        </Header>
    );

    renderCheckboxField = (name, label) => (
        <Field key={name}
               name={name}
               component={ReduxCheckboxField}
               componentLabel={Translate.string(label)}
               as={Checkbox} />
    );

    renderFormField = (name, label) => (
        <Field key={name}
               name={name}
               component={ReduxFormField}
               label={Translate.string(label)}
               as="input" />
    );

    renderFieldList = (fields) => fields.map(({name, label}) => this.renderFormField(name, label));

    renderCheckboxList = (checkboxes) => checkboxes.map(({name, label}) => this.renderCheckboxField(name, label));

    renderFormGroup = (children, key) => (
        <Form.Group widths="equal" key={key}>
            {children}
        </Form.Group>
    );

    renderGridColumn = (children, key) => (
        <Grid.Column key={key}>
            {children}
        </Grid.Column>
    );

    formDetails = [
        this.renderGridColumn([
            this.renderHeader('Contact'),
            ...this.renderFieldList([{
                name: 'ownerName',
                label: 'Owner'
            }, {
                name: 'keyLocation',
                label: 'Where is the key?'
            }, {
                name: 'telephone',
                label: 'Telephone'
            }]),
            this.renderHeader('Information'),
            this.renderFormGroup(
                this.renderFieldList([{
                    name: 'capacity',
                    label: 'Capacity (seats)'
                }, {
                    name: 'division',
                    label: 'Division'
                }]),
                'information'
            )
        ], 'col1'),
        this.renderGridColumn([
            this.renderHeader('Location'),
            ...this.renderFieldList([{
                name: 'name',
                label: 'Name'
            }, {
                name: 'site',
                label: 'Site'
            }]),
            this.renderFormGroup(
                this.renderFieldList([{
                    name: 'building',
                    label: 'Building'
                }, {
                    name: 'floor',
                    label: 'Floor',
                }, {
                    name: 'number',
                    label: 'Number'
                }]),
                'location_building'
            ),
            this.renderFormGroup(
                this.renderFieldList([{
                    name: 'longitude',
                    label: 'Longitute',
                }, {
                    name: 'latitude',
                    label: 'Latitude'
                }]),
                'location_coordinates'
            ),
            ...this.renderFieldList([{
                name: 'surfaceArea',
                label: 'Surface Area (m2)'
            }, {
                name: 'maxAdvanceDays',
                label: 'Maximum advance time for bookings (days)'
            }])
        ], 'col2'),
        this.renderGridColumn([
            this.renderHeader('Options'),
            ...this.renderCheckboxList([{
                name: 'isActive',
                label: 'Active'
            }, {
                name: 'isPublic',
                label: 'Public'
            }, {
                name: 'isAutoConfirm',
                label: 'Confirmations'
            }, {
                name: 'notificationsEnabled',
                label: 'Reminders Enabled'
            }]),
            ...this.renderFieldList([{
                name: 'dayReminder',
                label: 'Send Booking reminders X days before (single/day)'
            }, {
                name: 'weekReminder',
                label: 'Send Booking reminders X days before (weekly)'
            }, {
                name: 'monthReminder',
                label: 'Send Booking reminders X days before (monthly)'
            }])
        ], 'col3')
    ];

    renderModalContent = (fprops) => {
        const formProps = {onSubmit: fprops.handleSubmit};
        return (
            <>
                <Modal.Header>
                    <Translate>Edit Room Details</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Form id="room-form" {...formProps}>
                        <Grid columns={3}>
                            {this.formDetails}
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
        const props = {validate, onSubmit: this.handleSubmit};
        if (!room) {
            return <Dimmer active page><Loader /></Dimmer>;
        }
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <FinalForm {...props}
                           render={this.renderModalContent}
                           initialValues={room} />
            </Modal>
        );
    }
}

export default connect(
    null, dispatch => ({
        actions: bindActionCreators({
            updateRoom: roomActions.updateRoom,
        }, dispatch)
    })
)(RoomEditModal);
