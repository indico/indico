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
import updateRoomBasicDetailsURL from 'indico-url:rooms_new.admin_update_room';
import updateRoomEquipmentURL from 'indico-url:rooms_new.admin_update_room_equipment';
import updateRoomAttributesURL from 'indico-url:rooms_new.admin_update_room_attributes';
import updateRoomAvailabilityURL from 'indico-url:rooms_new.admin_update_room_availability';
import _ from 'lodash';
import React from 'react';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Button, Checkbox, Dimmer, Dropdown, Form, Grid, Header, Input, Loader, Message, Modal, TextArea} from 'semantic-ui-react';
import {Form as FinalForm, Field} from 'react-final-form';
import {FieldArray} from 'react-final-form-arrays';
import arrayMutators from 'final-form-arrays';
import shortid from 'shortid';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys, camelizeKeys} from 'indico/utils/case';
import {getChangedValues, ReduxCheckboxField, ReduxFormField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import PrincipalSearchField from 'indico/react/components/PrincipalSearchField';
import EquipmentList from './EquipmentList';
import DailyAvailability from './DailyAvailability';
import NonBookablePeriods from './NonBookablePeriods';
import SpriteImage from '../../components/SpriteImage';
import {actions as roomsActions} from '../../common/rooms';
import * as roomsSelectors from './selectors';
import {selectors as userSelectors} from '../user';

import './RoomEditModal.module.scss';


function isNumberInvalid(number) {
    return number !== null && (number > 30 || number < 1);
}

function validate(fields) {
    const {building, floor, number, capacity, attributes, surfaceArea, nonbookablePeriods, notificationBeforeDays,
           notificationBeforeDaysWeekly, notificationBeforeDaysMonthly} = fields;
    const errors = {};
    if (!building) {
        errors.building = Translate.string('Please provide a building.');
    }
    if (!floor) {
        errors.floor = Translate.string('Please provide a floor.');
    }
    if (!number) {
        errors.number = Translate.string('Please provide a number.');
    }
    if (!capacity) {
        errors.capacity = Translate.string('Please provide capacity.');
    }
    if (capacity !== null && capacity < 1) {
        errors.capacity = Translate.string('Please provide a valid capacity number.');
    }
    if (surfaceArea !== null && surfaceArea < 1) {
        errors.surfaceArea = Translate.string('Please provide a valid surface area number.');
    }
    if (isNumberInvalid(notificationBeforeDays)) {
        errors.notificationBeforeDays = Translate.string('Number of days must be between [1, 30]');
    }
    if (isNumberInvalid(notificationBeforeDaysWeekly)) {
        errors.notificationBeforeDaysWeekly = Translate.string('Number of days must be between [1, 30]');
    }
    if (isNumberInvalid(notificationBeforeDaysMonthly)) {
        errors.notificationBeforeDaysMonthly = Translate.string('Number of days must be between [1, 30]');
    }
    if (!attributes) {
        errors.attributes = Translate.string('Please provide an attribute value.');
    }
    if (nonbookablePeriods && nonbookablePeriods.some(x => !x.startDt || !x.endDt)) {
        errors.nonbookablePeriods = Translate.string('Please provide valid nonbookable periods.');
    }
    return errors;
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
        type: 'owner',
        name: 'ownerName',
        label: Translate.string('Owner')
    }, {
        type: 'input',
        name: 'keyLocation',
        label: Translate.string('Where is the key?'),
        inputType: 'text',
        required: false
    }, {
        type: 'input',
        name: 'telephone',
        label: Translate.string('Telephone'),
        inputType: 'text',
        required: false
    }, {
        type: 'header',
        label: Translate.string('Information')
    }, {
        type: 'formgroup',
        key: 'information',
        content: [{
            type: 'input',
            name: 'capacity',
            label: Translate.string('Capacity(seats)'),
            inputType: 'number',
            required: true
        }, {
            type: 'input',
            name: 'division',
            label: Translate.string('Division'),
            inputType: 'text',
            required: false
        }]
    }, {
        type: 'textarea',
        name: 'comments',
        label: Translate.string('Comments'),
        required: false
    }, {
        type: 'header',
        label: Translate.string('Daily availability'),
    }, {
        type: 'bookableHours',
    }], [{
        type: 'header',
        label: Translate.string('Location')
    }, {
        type: 'input',
        name: 'verboseName',
        label: Translate.string('Name'),
        inputType: 'text',
        required: false
    }, {
        type: 'input',
        name: 'site',
        label: Translate.string('Site'),
        inputType: 'text',
        required: false
    }, {
        type: 'formgroup',
        key: 'details',
        content: [{
            type: 'input',
            name: 'building',
            label: Translate.string('Building'),
            inputType: 'text',
            required: true
        }, {
            type: 'input',
            name: 'floor',
            label: Translate.string('Floor'),
            inputType: 'text',
            required: true
        }, {
            type: 'input',
            name: 'number',
            label: Translate.string('Number'),
            inputType: 'text',
            required: true
        }]
    }, {
        type: 'formgroup',
        key: 'coordinates',
        content: [{
            type: 'input',
            name: 'longitude',
            label: Translate.string('longitude'),
            inputType: 'number',
            required: false
        }, {
            type: 'input',
            name: 'latitude',
            label: Translate.string('latitude'),
            inputType: 'number',
            required: false
        }]
    }, {
        type: 'input',
        name: 'surfaceArea',
        label: Translate.string('Surface Area (m2)'),
        inputType: 'number',
        required: false
    }, {
        type: 'input',
        name: 'maxAdvanceDays',
        label: Translate.string('Maximum advance time for bookings (days)'),
        inputType: 'number',
        required: false
    }, {
        type: 'header',
        label: 'Options',
    }, {
        type: 'checkbox',
        name: 'isActive',
        label: Translate.string('Active')
    }, {
        type: 'checkbox',
        name: 'isReservable',
        label: Translate.string('Bookable')
    }, {
        type: 'checkbox',
        name: 'isAutoConfirm',
        label: Translate.string('Confirmation')
    }, {
        type: 'checkbox',
        name: 'notificationsEnabled',
        label: Translate.string('Reminders Enabled')
    }, {
        type: 'input',
        name: 'notificationBeforeDays',
        label: Translate.string('Send Booking reminders X days before (single/daily)'),
        inputType: 'number',
        required: false
    }, {
        type: 'input',
        name: 'notificationBeforeDaysWeekly',
        label: Translate.string('Send Booking reminders X days before (weekly)'),
        inputType: 'number',
        required: false
    }, {
        type: 'input',
        name: 'notificationBeforeDaysMonthly',
        label: Translate.string('Send Booking reminders X days before (monthly)'),
        inputType: 'number',
        required: false
    }], [{
        type: 'header',
        label: Translate.string('Custom Attributes')
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
        type: 'header',
        label: Translate.string('Nonbookable Periods'),
    }, {
        type: 'nonBookablePeriods'
    }, {
        type: 'message',
        content: Translate.string('Room has been successfully edited.')
    }]
];


class RoomEditModal extends React.Component {
    static propTypes = {
        equipmentTypes: PropTypes.arrayOf(PropTypes.object).isRequired,
        favoriteUsers: PropTypes.array.isRequired,
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,
    };

    state = {
        attributes: null,
        room: null,
        roomAttributes: null,
        roomAvailability: null,
        roomEquipment: null,
        submitSucceeded: false,
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
        const roomAvailability = camelizeKeys(response.data);
        roomAvailability.nonbookablePeriods.forEach(period => {
            period.key = shortid.generate();
        });
        roomAvailability.bookableHours.forEach(hours => {
            hours.key = shortid.generate();
        });

        this.setState({roomAvailability});
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

    handleSubmit = async (data, form) => {
        const {roomId, actions: {fetchRoom, fetchRoomDetails}} = this.props;
        const changedValues = getChangedValues(data, form);
        const basicDetails = _.omit(changedValues, ['attributes', 'bookableHours', 'nonbookablePeriods', 'availableEquipment']);
        if ('owner' in changedValues) {
            basicDetails.owner_id = changedValues.owner.id;
        }
        const {availableEquipment, nonbookablePeriods, bookableHours, attributes} = changedValues;

        const requests = [];
        if (!_.isEmpty(basicDetails)) {
            requests.push(indicoAxios.patch(updateRoomBasicDetailsURL({room_id: roomId}), snakifyKeys(basicDetails)));
        }
        if (availableEquipment) {
            requests.push(indicoAxios.post(updateRoomEquipmentURL({room_id: roomId}), {available_equipment: availableEquipment}));
        }
        if (attributes) {
            requests.push(indicoAxios.post(updateRoomAttributesURL({room_id: roomId}), {attributes}));
        }
        if (nonbookablePeriods || bookableHours) {
            requests.push(indicoAxios.post(updateRoomAvailabilityURL({room_id: roomId}), snakifyKeys(_.pick(changedValues, ['bookableHours', 'nonbookablePeriods']))));
        }

        try {
            await Promise.all(requests);
            this.setState({submitSucceeded: true});
            fetchRoom(roomId);
            fetchRoomDetails(roomId, true);
        } catch (e) {
            handleAxiosError(e);
            this.setState({submitSucceeded: false});
        }
    };


    renderImage = (position) => {
        return <SpriteImage key="image" pos={position} />;
    };

    renderAttributes = (content) => {
        const {attributes, roomAttributes} = this.state;
        if (!attributes || !roomAttributes) {
            return null;
        }
        const titles = _.fromPairs(attributes.map(x => [x.name, x.title]));
        return (
            <FieldArray key="attributes" name="attributes" isEqual={_.isEqual}>
                {({fields}) => {
                    if (!fields.value) {
                        return null;
                    }
                    const options = this.generateAttributeOptions(attributes, fields.value);
                    return (
                        <div>
                            <Dropdown className="icon room-edit-modal-add-btn"
                                      button
                                      text={content.placeholder}
                                      floating
                                      labeled
                                      icon="add"
                                      options={options}
                                      search
                                      disabled={options.length === 0}
                                      selectOnBlur={false}
                                      onChange={(__, {value: name}) => {
                                          fields.push({value: null, name});
                                      }} />
                            {fields.map((attribute, index) => (
                                <div key={attribute}>
                                    <Field label={titles[fields.value[index].name]}
                                           name={`${attribute}.value`}
                                           component={ReduxFormField}
                                           as={Input}
                                           isEqual={_.isEqual}
                                           required
                                           icon={{name: 'trash', color: 'red', link: true, onClick: () => fields.remove(index)}} />
                                </div>
                            ))}
                        </div>
                    );
                }}
            </FieldArray>
        );
    };

    renderColumn = (column, key) => (
        <Grid.Column key={key}>{column.map(this.renderContent)}</Grid.Column>
    );

    renderContent = (content, key) => {
        const {room, roomEquipment, submitSucceeded} = this.state;
        const {equipmentTypes, favoriteUsers} = this.props;
        if (!equipmentTypes) {
            return;
        }
        switch (content.type) {
            case 'header':
                return (
                    <Header key={key}>{content.label}</Header>
                );
            case 'input':
                return (
                    <Field key={key}
                           name={content.name}
                           component={ReduxFormField}
                           label={content.label}
                           required={content.required}
                           as="input"
                           type={content.inputType}
                           parse={(value) => {
                               return value === '' ? null : value;
                           }} />
                );
            case 'owner':
                return (
                    <Field key={key}
                           name="owner"
                           component={ReduxFormField}
                           as={PrincipalSearchField}
                           favoriteUsers={favoriteUsers}
                           label={content.label}
                           required />
                );
            case 'formgroup':
                return (
                    <Form.Group key={key}>
                        {content.content.map(this.renderContent)}
                    </Form.Group>
                );
            case 'checkbox':
                return (
                    <Field key={key}
                           name={content.name}
                           component={ReduxCheckboxField}
                           componentLabel={content.label}
                           as={Checkbox} />
                );
            case 'textarea':
                return (
                    <Field key={key}
                           name={content.name}
                           component={ReduxFormField}
                           label={content.label}
                           as={TextArea}
                           parse={null} />
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
                    <Field key={key}
                           name="availableEquipment"
                           component={ReduxFormField}
                           as={EquipmentList}
                           isEqual={_.isEqual}
                           componentLabel={Translate.string('Add new equipment')} />
                );
            case 'bookableHours':
                return (
                    <Field key={key}
                           name="bookableHours"
                           component={ReduxFormField}
                           as={DailyAvailability}
                           isEqual={_.isEqual} />
                );
            case 'nonBookablePeriods':
                return (
                    <Field key={key}
                           name="nonbookablePeriods"
                           component={ReduxFormField}
                           as={NonBookablePeriods}
                           isEqual={_.isEqual} />
                );
            case 'message':
                return (
                    <Message key={key}
                             styleName="success-message"
                             positive
                             hidden={!submitSucceeded}>
                        {content.content}
                    </Message>
                );
        }
    };


    renderModalContent = (fprops) => {
        const formProps = {onSubmit: fprops.handleSubmit};
        const {hasValidationErrors, pristine, submitting, submitSucceeded} = fprops;
        const {onClose} = this.props;
        return (
            <>
                <Modal.Header>
                    {Translate.string('Edit Room Details')}
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
                            primary
                            disabled={pristine || submitting || submitSucceeded || hasValidationErrors}
                            loading={submitting}>
                        <Translate>Save</Translate>
                    </Button>
                </Modal.Actions>
            </>
        );
    };

    generateAttributeOptions = (attributes, arrayFields) => {
        const fieldNames = arrayFields.map(field => field.name);
        return attributes
            .map(attr => ({key: attr.name, text: attr.title, value: attr.name}))
            .filter(attr => !fieldNames.includes(attr.key));
    };

    render() {
        const {room, roomAttributes, attributes, roomEquipment, roomAvailability} = this.state;
        const props = {validate, onSubmit: this.handleSubmit};
        if (!room || !attributes || !roomAttributes || !roomEquipment) {
            return <Dimmer active page><Loader /></Dimmer>;
        }
        const initialValues = {
            ...room,
            attributes: roomAttributes,
            ...roomEquipment,
            ...roomAvailability,
        };
        return (
            <>
                <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                    <FinalForm {...props}
                               render={this.renderModalContent}
                               initialValues={initialValues}
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
            fetchRoom: roomsActions.fetchRoom,
            fetchRoomDetails: roomsActions.fetchDetails,
        }, dispatch),
    }),
)(RoomEditModal);
