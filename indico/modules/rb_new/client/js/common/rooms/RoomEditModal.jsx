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

import fetchRoomURL from 'indico-url:rooms_new.admin_room';
import fetchRoomAttributesURL from 'indico-url:rooms_new.admin_room_attributes';
import fetchAttributesURL from 'indico-url:rooms_new.admin_attributes';
import fetchRoomAvailabilityURL from 'indico-url:rooms_new.admin_room_availability';
import fetchRoomEquipmentURL from 'indico-url:rooms_new.admin_room_equipment';
import _ from 'lodash';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {Button, Checkbox, Dimmer, Dropdown, Form, Grid, Header, Input, Loader, Modal, TextArea} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {FieldArray} from 'react-final-form-arrays';
import arrayMutators from "final-form-arrays";
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import camelizeKeys from 'indico/utils/camelize';
import {ReduxCheckboxField, ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import EquipmentList from './EquipmentList';
import DailyAvailability from './DailyAvailability';
import NonBookablePeriods from './NonBookablePeriods';
import SpriteImage from '../../components/SpriteImage';
import * as roomsSelectors from './selectors';
import * as roomActions from './actions';
import {selectors as userSelectors} from '../user';

import './RoomEditModal.module.scss';


function validate() {
}

const columns = [
    [{
        type: 'header',
        label: Translate.string('Image')
    }, {
        type: 'image',
    }, {
        type: 'header',
        label: Translate.string('Contact')
    }, {
        type: 'principal',
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
    }, {
        type: 'textarea',
        name: 'comments',
        label: Translate.string('Comments'),
    }, {
        type: 'headerWithButton',
        label: Translate.string('Daily availability'),
        action: 'dailyHours'
    }, {
        type: 'timeRange',
    }], [{
        type: 'header',
        label: Translate.string('Location')
    }, {
        type: 'input',
        name: 'verboseName',
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
    }, {
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
    }], [{
        type: 'header',
        label: 'Custom Attributes'
    }, {
        type: 'attributes',
        placeholder: Translate.string('Add new attributes'),
    }, {
        type: 'header',
        label: Translate.string('Equipment Available')
    }, {
        type: 'equipment',
        placeholder: Translate.string('Add new equipment')
    }, {
        type: 'headerWithButton',
        label: Translate.string('Nonbookable Hours'),
        action: 'nonBookableHours'
    }, {
        type: 'dateRange'
    }]];


class RoomEditModal extends React.Component {
    static propTypes = {
        equipmentTypes: PropTypes.arrayOf(PropTypes.object).isRequired,
        favoriteUsers: PropTypes.array.isRequired,
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,
        actions: PropTypes.exact({
            updateRoom: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {
        attributes: null,
        room: null,
        roomAttributes: null,
        roomAvailability: null,
        roomEquipment: null,
    };

    componentDidMount() {
        this.fetchDetailedRoom();
        this.fetchRoomAttributes();
        this.fetchAttributes();
        this.fetchRoomAvailability();
        this.fetchRoomEquipment();
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

    async fetchRoomAttributes() {
        const {roomId} = this.props;
        let response;
        try {
            response = await indicoAxios.get(fetchRoomAttributesURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        this.setState({roomAttributes: response.data});
    }

    async fetchAttributes() {
        let response;
        try {
            response = await indicoAxios.get(fetchAttributesURL());
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        this.setState({attributes: response.data});
    }


    async fetchRoomAvailability() {
        const {roomId} = this.props;
        let response;
        try {
            response = await indicoAxios.get(fetchRoomAvailabilityURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        console.warn(camelizeKeys(response.data));
        this.setState({roomAvailability: camelizeKeys(response.data)});
    }

    async fetchRoomEquipment() {
        const {roomId} = this.props;
        let response;
        try {
            response = await indicoAxios.get(fetchRoomEquipmentURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        this.setState({roomEquipment: camelizeKeys(response.data)});
    }

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    handleSubmit = async (formData) => {
        const {actions: {updateRoom}, room: {id}} = this.props;
        const rv = await updateRoom(id, formData);
        if (rv.error) {
            return rv.error;
        }
    };

    renderImage = (position) => {
        return <SpriteImage pos={position} />;
    };

    renderAttributes = (content) => {
        const {attributes} = this.state;
        if (!attributes) {
            return;
        }
        return (
            <FieldArray name="attributes">
                {({fields}) => {
                    const options = this.generateAttributeOptions(attributes, fields.value);
                    return (
                        <div>
                            <Dropdown button
                                    text={content.placeholder}
                                    className="icon"
                                    floating
                                    labeled
                                    icon="add"
                                    options={options}
                                    search
                                    disabled={options.length === 0}
                                    selectOnBlur={false}
                                    onChange={(event, values) => fields.push({title: values.value, value: null})} />
                            {fields.map((attribute, index) => (
                                <div key={attribute}>
                                    <Field label={fields.value[index].title}
                                        name={`${attribute}.value`}
                                        component={ReduxFormField}
                                        as={Input}
                                        isEqual={_.isEqual}
                                        icon={{name: 'trash', color: 'red', link: true, onClick: () => fields.remove(index)}} />
                                </div>
                            ))}
                        </div>
                )}}
            </FieldArray>
        );
    };

    renderEquipmentList = ({input, ...props}) => {
        return (
            <ReduxFormField {...props}
                            input={input}
                            as={EquipmentList}
                            componentLabel={Translate.string('Add new equipment')} />
        );
    };

    renderHours = ({input, ...props}) => {
        return (
            <ReduxFormField {...props}
                            input={input}
                            as={DailyAvailability} />
        );
    };

    renderPeriods = ({input, ...props}) => {
        return (
            <ReduxFormField {...props}
                            input={input}
                            as={NonBookablePeriods} />
        );
    };

    renderPrincipalSearchField = (props) => {
        const {favoriteUsers} = this.props;
        return (
            <ReduxFormField {...props}
                            favoriteUsers={favoriteUsers}
                            as={PrincipalSearchField}
                            label={Translate.string('Owner')} />
        );
    };

    renderColumn = (column, key) => (
        <Grid.Column key={key}>{column.map(this.renderContent)}</Grid.Column>
    );

    renderContent = (content) => {
        const {room, roomEquipment, roomAvailability} = this.state;
        const {equipmentTypes} = this.props;
        if (!equipmentTypes) {
            return;
        }
        switch (content.type) {
            case 'header':
                return (
                    <Header key={content.label}>{content.label}</Header>
                );
            case 'input':
                return (
                    <Field key={content.name}
                           name={content.name}
                           component={ReduxFormField}
                           label={content.label}
                           as="input" />
                );
            case 'principal':
                return (
                    <Field name="owner"
                           render={this.renderPrincipalSearchField} />
                );
            case 'formgroup':
                return (
                    <Form.Group key={content.key}>
                        {content.content.map(this.renderContent)}
                    </Form.Group>
                );
            case 'checkbox':
                return (
                    <Field key={content.name}
                           name={content.name}
                           component={ReduxCheckboxField}
                           componentLabel={content.label}
                           as={Checkbox} />
                );
            case 'textarea':
                return (
                    <Field key={content.name}
                           name={content.name}
                           component={ReduxFormField}
                           label={content.label}
                           as={TextArea} />
                );
            case 'image':
                return this.renderImage(room.spritePosition);
            case 'attributes':
                return this.renderAttributes(content);
            case 'equipment':
                if (!roomEquipment && equipmentTypes) {
                    return;
                }
                return (
                    <Field name="availableEquipment"
                           isEqual={_.isEqual}
                           render={this.renderEquipmentList} />
                );
            case 'headerWithButton':
                return (
                    <Header key={content.label} styleName="button-header">
                        {content.label}
                        <Button size="small" onClick={content.action === 'dailyHours' ? null : null}>Add</Button>
                    </Header>
                );
            case 'timeRange':
                if (!roomAvailability || !roomAvailability.bookableHours.length) {
                    return <div key={1}>No bookable hours found</div>;
                }

                return (
                    <Field name="bookableHours"
                           isEqual={_.isEqual}
                           render={this.renderHours} />
                );
            case 'dateRange':
                if (!roomAvailability || !roomAvailability.nonbookablePeriods.length) {
                    return <div key={2}>No non bookable periods found </div>;
                }

                return (
                    <Field name="nonbookablePeriods"
                           isEqual={_.isEqual}
                           render={this.renderPeriods} />
                );
        }
    };


    renderModalContent = (fprops) => {
        const formProps = {onSubmit: fprops.handleSubmit};
        const {onClose} = this.props;
        return (
            <>
                <Modal.Header>
                    <Translate>Edit Room Details</Translate>
                </Modal.Header>
                <Modal.Content scrolling>
                    <Form id="room-form" {...formProps}>
                        <Grid columns={3}>
                            {columns.map(this.renderColumn)}
                        </Grid>
                    </Form>
                </Modal.Content>
                <Modal.Actions>
                    <Button onClick={onClose}>
                        Cancel
                    </Button>
                    <Button type="submit"
                            form="room-form"
                            primary>
                        <Translate>Save</Translate>
                    </Button>
                </Modal.Actions>
            </>
        );
    };

    addAttribute = (newAttributeName) => {
        const {roomAttributes} = this.state;
        const newAttribute = {
            [newAttributeName]: null
        };
        this.setState({roomAttributes: {...roomAttributes, ...newAttribute}});
    };

    generateAttributeOptions = (attributes, arrayFields) => {
        const fieldNames = arrayFields.map(field => field.title);
        const options = attributes.map((key) => ({key: key.name, text: key.title, value: key.name})).filter(attr => !fieldNames.includes(attr.key));
        return options;
    };


    render() {
        const {room, roomAttributes, attributes, roomEquipment, roomAvailability} = this.state;
        const props = {validate, onSubmit: this.handleSubmit};
        if (!room || !attributes || !roomAttributes || !roomEquipment) {
            return <Dimmer active page><Loader /></Dimmer>;
        }
        return (
            <>
                <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                    <FinalForm {...props}
                               render={this.renderModalContent}
                               initialValues={{...room, attributes: roomAttributes, ...roomEquipment, ...roomAvailability}}
                               mutators={{
                                   ...arrayMutators
                               }} />
                </Modal>
            </>
        );
    }
}

export default connect(
    (state) => ({
        equipmentTypes: roomsSelectors.getEquipmentTypes(state),
        favoriteUsers: userSelectors.getFavoriteUsers(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            updateRoom: roomActions.updateRoom,
        }, dispatch)
    })
)(RoomEditModal);
