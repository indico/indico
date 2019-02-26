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
import {
    Button, Checkbox, Dimmer, Dropdown, Form, Grid, Header, Input, Loader, Message, Modal, TextArea
} from 'semantic-ui-react';
import {Form as FinalForm, Field, FormSpy} from 'react-final-form';
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
import {actions as userActions, selectors as userSelectors} from '../../common/user';
import * as roomsSelectors from './selectors';

import './RoomEditModal.module.scss';


function isInvalidNotificationPeriod(days) {
    return days !== null && (days > 30 || days < 1);
}

function validate(fields) {
    const {
        building, floor, number, capacity, surfaceArea, maxAdvanceDays, bookingLimitDays, nonbookablePeriods,
        notificationBeforeDays, notificationBeforeDaysWeekly, notificationBeforeDaysMonthly,
    } = fields;
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
    if (capacity < 1) {
        errors.capacity = Translate.string('Please provide a valid capacity number.');
    }
    if (surfaceArea < 1) {
        errors.surfaceArea = Translate.string('Please provide a valid surface area.');
    }
    if (maxAdvanceDays !== null && maxAdvanceDays < 1) {
        errors.maxAdvanceDays = Translate.string('The max. advance booking time must be at least 1 day or empty.');
    }
    if (bookingLimitDays !== null && bookingLimitDays < 1) {
        errors.bookingLimitDays = Translate.string('The max. booking duration must be at least 1 day or empty.');
    }
    if (isInvalidNotificationPeriod(notificationBeforeDays)) {
        errors.notificationBeforeDays = Translate.string('Number of days must be between 1 and 30');
    }
    if (isInvalidNotificationPeriod(notificationBeforeDaysWeekly)) {
        errors.notificationBeforeDaysWeekly = Translate.string('Number of days must be between 1 and 30');
    }
    if (isInvalidNotificationPeriod(notificationBeforeDaysMonthly)) {
        errors.notificationBeforeDaysMonthly = Translate.string('Number of days must be between 1 and 30');
    }
    if (nonbookablePeriods && nonbookablePeriods.some(x => !x.startDt || !x.endDt)) {
        errors.nonbookablePeriods = Translate.string('Please provide valid non-bookable periods.');
    }
    return errors;
}

const columns = [
    // left
    [{
        type: 'header',
        label: Translate.string('Photo')
    }, {
        type: 'photo',
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
        required: false
    }, {
        type: 'input',
        name: 'telephone',
        label: Translate.string('Telephone'),
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
            label: Translate.string('Capacity'),
            inputArgs: {
                type: 'number',
                min: 1,
            },
            required: true
        }, {
            type: 'input',
            name: 'division',
            label: Translate.string('Division'),
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
    }],
    // center
    [{
        type: 'header',
        label: Translate.string('Location')
    }, {
        type: 'input',
        name: 'verboseName',
        label: Translate.string('Name'),
        required: false
    }, {
        type: 'input',
        name: 'site',
        label: Translate.string('Site'),
        required: false
    }, {
        type: 'formgroup',
        key: 'details',
        content: [{
            type: 'input',
            name: 'building',
            label: Translate.string('Building'),
            required: true
        }, {
            type: 'input',
            name: 'floor',
            label: Translate.string('Floor'),
            required: true
        }, {
            type: 'input',
            name: 'number',
            label: Translate.string('Number'),
            required: true
        }]
    }, {
        type: 'formgroup',
        key: 'coordinates',
        content: [{
            type: 'input',
            name: 'longitude',
            label: Translate.string('Longitude'),
            inputArgs: {
                type: 'number',
            },
            required: false
        }, {
            type: 'input',
            name: 'latitude',
            label: Translate.string('Latitude'),
            inputArgs: {
                type: 'number',
            },
            required: false
        }]
    }, {
        type: 'input',
        name: 'surfaceArea',
        label: Translate.string('Surface Area (m²)'),
        inputArgs: {
            type: 'number',
            min: 0,
        },
        required: false
    }, {
        type: 'input',
        name: 'maxAdvanceDays',
        label: Translate.string('Maximum advance time for bookings (days)'),
        inputArgs: {
            type: 'number',
            min: 1,
        },
        required: false
    }, {
        type: 'input',
        name: 'bookingLimitDays',
        label: Translate.string('Max duration of a booking (day)'),
        inputArgs: {
            type: 'number',
            min: 1,
        },
        required: false
    }, {
        type: 'header',
        label: 'Options',
    }, {
        type: 'checkbox',
        name: 'isReservable',
        label: Translate.string('Bookable')
    }, {
        type: 'checkbox',
        name: 'reservationsNeedConfirmation',
        label: Translate.string('Require confirmation (pre-bookings)')
    }, {
        type: 'checkbox',
        name: 'notificationsEnabled',
        label: Translate.string('Reminders enabled')
    }, {
        type: 'input',
        name: 'notificationBeforeDays',
        label: Translate.string('Send Booking reminders X days before (single/daily)'),
        inputArgs: {
            type: 'number',
            min: 1,
            max: 30,
        },
        required: false
    }, {
        type: 'input',
        name: 'notificationBeforeDaysWeekly',
        label: Translate.string('Send Booking reminders X days before (weekly)'),
        inputArgs: {
            type: 'number',
            min: 1,
            max: 30,
        },
        required: false
    }, {
        type: 'input',
        name: 'notificationBeforeDaysMonthly',
        label: Translate.string('Send Booking reminders X days before (monthly)'),
        inputArgs: {
            type: 'number',
            min: 1,
            max: 30,
        },
        required: false
    }],
    // right
    [{
        type: 'header',
        label: Translate.string('Custom attributes')
    }, {
        type: 'attributes',
        placeholder: Translate.string('Add new attributes'),
    }, {
        type: 'header',
        label: Translate.string('Equipment available')
    }, {
        type: 'equipment',
        placeholder: Translate.string('Add new equipment')
    }, {
        type: 'header',
        label: Translate.string('Non-bookable periods'),
    }, {
        type: 'nonBookablePeriods'
    }]
];


class RoomEditModal extends React.Component {
    static propTypes = {
        equipmentTypes: PropTypes.arrayOf(PropTypes.object).isRequired,
        favoriteUsers: PropTypes.array.isRequired,
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number.isRequired,
        actions: PropTypes.exact({
            fetchRoom: PropTypes.func.isRequired,
            fetchRoomPermissions: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    state = {
        attributes: null,
        room: null,
        roomAttributes: null,
        roomAvailability: null,
        roomEquipment: null,
        submitState: '',
        closing: false,
    };

    componentDidMount() {
        this.fetchAttributes();
        this.fetchRoomData();
    }

    get loadingInitialData() {
        const {attributes, room, roomAttributes, roomEquipment, roomAvailability} = this.state;
        return !attributes || !room || !roomAttributes || !roomEquipment || !roomAvailability;
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

    async fetchRoomData() {
        const reqs = [
            this.fetchDetailedRoom(),
            this.fetchRoomAttributes(),
            this.fetchRoomAvailability(),
            this.fetchRoomEquipment(),
        ];
        this.setState(Object.assign(...await Promise.all(reqs)));
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
        return {room: camelizeKeys(response.data)};
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
        return {roomAttributes: response.data};
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

        return {roomAvailability};
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
        return {roomEquipment: camelizeKeys(response.data)};
    }

    handleCloseModal = async () => {
        const {onClose, roomId, actions: {fetchRoom, fetchRoomDetails, fetchRoomPermissions}} = this.props;
        this.setState({closing: true});
        await Promise.all([
            fetchRoom(roomId),
            fetchRoomPermissions(roomId),
            fetchRoomDetails(roomId, true)
        ]);
        onClose();
    };

    handleSubmit = async (data, form) => {
        const {roomId} = this.props;
        const changedValues = getChangedValues(data, form);
        const basicDetails = _.omit(changedValues, ['attributes', 'bookableHours', 'nonbookablePeriods', 'availableEquipment', 'owner']);
        if ('owner' in changedValues) {
            basicDetails.owner_id = changedValues.owner.id;
        }
        const {availableEquipment, nonbookablePeriods, bookableHours, attributes} = changedValues;

        let submitState = 'success';
        try {
            await this.saveBasicDetails(roomId, basicDetails);
            await this.saveEquipment(roomId, availableEquipment);
            await this.saveAttributes(roomId, attributes);
            await this.saveAvailability(roomId, changedValues, nonbookablePeriods, bookableHours);
        } catch (e) {
            handleAxiosError(e);
            submitState = 'error';
        }
        // reload room so the form gets new initialValues
        await this.fetchRoomData();
        this.setState({submitState});
    };

    async saveBasicDetails(roomId, basicDetails) {
        if (!_.isEmpty(basicDetails)) {
            await indicoAxios.patch(updateRoomBasicDetailsURL({room_id: roomId}), snakifyKeys(basicDetails));
        }
    }

    async saveEquipment(roomId, availableEquipment) {
        if (availableEquipment) {
            const params = {available_equipment: availableEquipment};
            await indicoAxios.post(updateRoomEquipmentURL({room_id: roomId}), params);
        }
    }

    async saveAttributes(roomId, attributes) {
        if (attributes) {
            await indicoAxios.post(updateRoomAttributesURL({room_id: roomId}), {attributes});
        }
    }

    async saveAvailability(roomId, changedValues, nonbookablePeriods, bookableHours) {
        if (nonbookablePeriods || bookableHours) {
            const params = snakifyKeys(_.pick(changedValues, ['bookableHours', 'nonbookablePeriods']));
            await indicoAxios.post(updateRoomAvailabilityURL({room_id: roomId}), params);
        }
    }

    renderPhoto = (position) => {
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
                            {fields.length === 0 && <div><Translate>No custom attributes found</Translate></div>}
                        </div>
                    );
                }}
            </FieldArray>
        );
    };

    renderContent = (content, key) => {
        const {room, roomEquipment} = this.state;
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
                           parse={(value) => value || null}
                           {...(content.inputArgs || {type: 'text'})} />
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
            case 'photo':
                return this.renderPhoto(room.spritePosition);
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
                           isEqual={_.isEqual}
                           format={(value) => {
                               return value === null ? [] : value;
                           }} />
                );
            case 'nonBookablePeriods':
                return (
                    <Field key={key}
                           name="nonbookablePeriods"
                           component={ReduxFormField}
                           as={NonBookablePeriods}
                           isEqual={_.isEqual}
                           format={(value) => {
                               return value === null ? [] : value;
                           }} />
                );
        }
    };

    renderModalContent = (fprops) => {
        const {hasValidationErrors, pristine, submitting} = fprops;
        const {submitState} = this.state;
        return (
            <>
                <Modal.Header>
                    {Translate.string('Edit Room Details')}
                </Modal.Header>
                <Modal.Content scrolling>
                    <Form id="room-form"
                          onSubmit={fprops.handleSubmit}>
                        <Grid columns={3}>
                            <Grid.Column>{columns[0].map(this.renderContent)}</Grid.Column>
                            <Grid.Column>{columns[1].map(this.renderContent)}</Grid.Column>
                            <Grid.Column>
                                {columns[2].map(this.renderContent)}
                                <Message styleName="submit-message" positive hidden={submitState !== 'success'}>
                                    <Translate>
                                        Room has been successfully updated.
                                    </Translate>
                                </Message>
                                <Message styleName="submit-message" negative hidden={submitState !== 'error'}>
                                    <Translate>
                                        Room could not be updated.
                                    </Translate>
                                </Message>
                            </Grid.Column>
                        </Grid>
                    </Form>
                </Modal.Content>
                <Modal.Actions>
                    <Button onClick={this.handleCloseModal}>
                        <Translate>Cancel</Translate>
                    </Button>
                    <Button type="submit"
                            form="room-form"
                            primary
                            disabled={pristine || submitting || hasValidationErrors}
                            loading={submitting}>
                        <Translate>Save</Translate>
                    </Button>
                </Modal.Actions>
                <FormSpy subscription={{dirty: true}}
                         onChange={({dirty}) => {
                             if (dirty) {
                                 this.setState({submitState: ''});
                             }
                         }} />
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
        const {room, roomAttributes, roomEquipment, roomAvailability, closing} = this.state;
        if (this.loadingInitialData || closing) {
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
                    <FinalForm validate={validate}
                               onSubmit={this.handleSubmit}
                               render={this.renderModalContent}
                               initialValues={initialValues}
                               mutators={{...arrayMutators}} />
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
            fetchRoomPermissions: userActions.fetchRoomPermissions,
            fetchRoomDetails: roomsActions.fetchDetails,
        }, dispatch),
    }),
)(RoomEditModal);
