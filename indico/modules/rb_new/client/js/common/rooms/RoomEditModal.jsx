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
import {bindActionCreators} from "redux";

function validate({}) {
};

const columns = [[
    {
        type: 'header',
        label: Translate.string('Contact')
    }, {
        type: 'input',
        name: 'ownerName',
        label: Translate.string('Owner')
    }, {
        type: 'input',
        name: 'keyLocation',
        label: Translate.string('Where is the key?')
    }, {
        type: 'input',
        name: 'telephone',
        label: Translate.string('Telephone')
    }, {
        type: 'header',
        label: Translate.string('Information')
    }, {
        type: 'formgroup',
        key: 'information',
        content: [{
            type: 'input',
            name: 'capacity',
            label: Translate.string('Capacity(seats)')
        }, {
            type: 'input',
            name: 'division',
            label: Translate.string('Division')
        }]
    }], [{
        type: 'header',
        label: Translate.string('Location')
    }, {
        type: 'input',
        name: 'name',
        label: Translate.string('Name')
    }, {
        type: 'input',
        name: 'site',
        label: Translate.string('Site')
    }, {
        type: 'formgroup',
        key: 'details',
        content: [{
            type: 'input',
            name: 'building',
            label: Translate.string('Building')
        }, {
            type: 'input',
            name: 'floor',
            label: Translate.string('Floor')
        }, {
            type: 'input',
            name: 'number',
            label: Translate.string('Number')
        }]
    }, {
        type: 'formgroup',
        key: 'coordinates',
        content: [{
            type: 'input',
            name: 'longitude',
            label: Translate.string('longitude')
        }, {
            type: 'input',
            name: 'latitude',
            label: Translate.string('latitude')
        }]
    }, {
        type: 'input',
        name: 'surfaceArea',
        label: Translate.string('Surface Area (m2)')
    }, {
        type: 'input',
        name: 'maxAdvanceDays',
        label: Translate.string('Maximum advance time for bookings (days)')
    }], [{
        type: 'header',
        label: 'Options',
    }, {
        type: 'checkbox',
        name: 'isActive',
        label: Translate.string('Active')
    }, {
        type: 'checkbox',
        name: 'isPublic',
        label: Translate.string('Public')
    }, {
        type: 'checkbox',
        name: 'isAutoConfirm',
        label: Translate.string('Confirmation')
    }, {
        type: 'checkbox',
        name: 'reminders',
        label: Translate.string('Reminders Enabled')
    }, {
        type: 'input',
        name: 'dayReminder',
        label: Translate.string('Send Booking reminders X days before (single/day)')
    }, {
        type: 'input',
        name: 'weekReminder',
        label: Translate.string('Send Booking reminders X days before (weekly)')
    }, {
        type: 'input',
        name: 'monthReminder',
        label: Translate.string('Send Booking reminders X days before (monthly)')
    }]];

class RoomEditModal extends React.Component {
    static propTypes = {
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,
        actions: PropTypes.exact({
            updateRoom: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {
        room: null
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

    handleSubmit = async (formData) => {
        const {actions: {updateRoom}, room: {id}} = this.props;
        let rv = await updateRoom(id, formData);
        if(rv.error){
            return rv.error;
        }
    };

    renderColumn = (column, key) => (
        <Grid.Column key={key}>{column.map(this.renderContent)}</Grid.Column>
    );

    renderContent = (content) => {
        switch (content.type) {
            case 'header':
                return (
                    <Header key={content.label}>{content.label}</Header>);
            case 'input':
                return (
                    <Field key={content.name}
                           name={content.name}
                           component={ReduxFormField}
                           label={content.label}
                           as="input" />);
            case 'formgroup':
                return (
                    <Form.Group key={content.key}>
                        {content.content.map(this.renderContent)}
                    </Form.Group>);
            case 'checkbox':
                return (
                    <Field key={content.name}
                           name={content.name}
                           component={ReduxCheckboxField}
                           componentLabel={content.label}
                           as={Checkbox} />);
        }
    };


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
                            {columns.map(this.renderColumn)}
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
    null,
    dispatch => ({
        actions: bindActionCreators({
            updateRoom: roomActions.updateRoom,
        }, dispatch)
    })
)(RoomEditModal);
