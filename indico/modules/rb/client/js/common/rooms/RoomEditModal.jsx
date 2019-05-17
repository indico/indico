// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import roomURL from 'indico-url:rb.admin_room';
import roomsURL from 'indico-url:rb.admin_rooms';
import fetchRoomAttributesURL from 'indico-url:rb.admin_room_attributes';
import fetchAttributesURL from 'indico-url:rb.admin_attributes';
import fetchRoomAvailabilityURL from 'indico-url:rb.admin_room_availability';
import fetchRoomEquipmentURL from 'indico-url:rb.admin_room_equipment';
import updateRoomEquipmentURL from 'indico-url:rb.admin_update_room_equipment';
import updateRoomAttributesURL from 'indico-url:rb.admin_update_room_attributes';
import updateRoomAvailabilityURL from 'indico-url:rb.admin_update_room_availability';

import _ from 'lodash';
import React from 'react';
import {bindActionCreators} from 'redux';
import PropTypes from 'prop-types';
import {connect} from 'react-redux';
import {Button, Dimmer, Dropdown, Form, Grid, Header, Loader, Message, Modal} from 'semantic-ui-react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {FieldArray} from 'react-final-form-arrays';
import arrayMutators from 'final-form-arrays';
import shortid from 'shortid';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys, camelizeKeys} from 'indico/utils/case';
import {
    FieldCondition, getChangedValues, handleSubmitError, FinalCheckbox, FinalField, FinalInput, FinalTextArea,
} from 'indico/react/forms';
import {FavoritesProvider} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {FinalEmailList, FinalPrincipal} from 'indico/react/components';
import EquipmentList from './EquipmentList';
import DailyAvailability from './DailyAvailability';
import NonBookablePeriods from './NonBookablePeriods';
import RoomPhoto from './RoomPhoto';
import {actions as roomsActions} from '../../common/rooms';
import {actions as userActions} from '../../common/user';
import * as roomsSelectors from './selectors';

import './RoomEditModal.module.scss';


function isInvalidNotificationPeriod(days) {
    return days !== null && (days > 30 || days < 1);
}

function validate(fields) {
    const {
        building, floor, number, capacity, surfaceArea, maxAdvanceDays, bookingLimitDays, nonbookablePeriods, owner
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
    if (surfaceArea && surfaceArea < 1) {
        errors.surfaceArea = Translate.string('Please provide a valid surface area.');
    }
    if (maxAdvanceDays !== null && maxAdvanceDays < 1) {
        errors.maxAdvanceDays = Translate.string('The max. advance booking time must be at least 1 day or empty.');
    }
    if (bookingLimitDays !== null && bookingLimitDays < 1) {
        errors.bookingLimitDays = Translate.string('The max. booking duration must be at least 1 day or empty.');
    }
    const notificationPeriodFields = [
        'notificationBeforeDays',
        'notificationBeforeDaysWeekly',
        'notificationBeforeDaysMonthly',
        'notificationBeforeEndDaily',
        'notificationBeforeEndWeekly',
        'notificationBeforeEndMonthly',
    ];

    notificationPeriodFields.forEach((field) => {
        const value = fields[field];
        if (isInvalidNotificationPeriod(value)) {
            errors[field] = Translate.string('Number of days must be between 1 and 30');
        }
    });

    if (nonbookablePeriods && nonbookablePeriods.some(x => !x.startDt || !x.endDt)) {
        errors.nonbookablePeriods = Translate.string('Please provide valid non-bookable periods.');
    }
    if (!owner) {
        errors.owner = Translate.string('You need to specify the owner of the room.');
    }
    return errors;
}

const columns = [
    // left
    [{
        type: 'header',
        key: 'photo',
        label: Translate.string('Photo')
    }, {
        type: 'photo',
    }, {
        type: 'header',
        label: Translate.string('Contact')
    }, {
        type: 'owner',
        name: 'owner',
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
                fluid: true,
            },
            required: true
        }, {
            type: 'input',
            name: 'division',
            label: Translate.string('Division'),
            required: false,
            inputArgs: {
                fluid: true,
            },
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
        required: false,
        inputArgs: {
            nullIfEmpty: true
        },
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
            required: true,
            inputArgs: {
                fluid: true,
            },
        }, {
            type: 'input',
            name: 'floor',
            label: Translate.string('Floor'),
            required: true,
            inputArgs: {
                fluid: true,
            },
        }, {
            type: 'input',
            name: 'number',
            label: Translate.string('Number'),
            required: true,
            inputArgs: {
                fluid: true,
            },
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
                fluid: true,
            },
            required: false
        }, {
            type: 'input',
            name: 'latitude',
            label: Translate.string('Latitude'),
            inputArgs: {
                type: 'number',
                fluid: true,
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
        label: Translate.string('Options'),
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
        type: 'checkbox',
        name: 'endNotificationsEnabled',
        label: Translate.string('Reminders of finishing bookings enabled')
    }, {
        type: 'header',
        label: Translate.string('Notifications')
    }, {
        type: 'emails',
        name: 'notificationEmails',
        label: Translate.string('Notification emails'),
    }, {
        type: 'formgroup',
        key: 'notifications',
        dependsOn: 'notificationsEnabled',
        label: Translate.string('How many days in advance booking reminders should be sent'),
        content: [{
            type: 'input',
            name: 'notificationBeforeDays',
            label: Translate.string('Single/Daily'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }, {
            type: 'input',
            name: 'notificationBeforeDaysWeekly',
            label: Translate.string('Weekly'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }, {
            type: 'input',
            name: 'notificationBeforeDaysMonthly',
            label: Translate.string('Monthly'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }]
    }, {
        type: 'formgroup',
        key: 'notificationsOfFinishingBookings',
        dependsOn: 'endNotificationsEnabled',
        label: Translate.string('How many days before the end of a booking should reminders be sent'),
        content: [{
            type: 'input',
            name: 'endNotificationDaily',
            label: Translate.string('Daily'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }, {
            type: 'input',
            name: 'endNotificationWeekly',
            label: Translate.string('Weekly'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }, {
            type: 'input',
            name: 'endNotificationMonthly',
            label: Translate.string('Monthly'),
            inputArgs: {
                type: 'number',
                min: 1,
                max: 30,
                fluid: true,
            },
            required: false
        }]
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
        onClose: PropTypes.func.isRequired,
        roomId: PropTypes.number,
        locationId: PropTypes.number,
        afterCreation: PropTypes.bool,
        actions: PropTypes.exact({
            fetchEquipmentTypes: PropTypes.func.isRequired,
            fetchRoom: PropTypes.func.isRequired,
            fetchRoomPermissions: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
        }).isRequired,
    };

    static defaultProps = {
        roomId: null,
        locationId: null,
        afterCreation: false,
    };

    state = {
        newRoomId: null,
        attributes: null,
        room: null,
        roomAttributes: null,
        roomAvailability: null,
        roomEquipment: null,
        submitState: '',
        wasEverDirty: false,
        wasEverSaved: false,
        closing: false,
    };

    componentDidMount() {
        this.fetchAttributes();
        if (this.newRoom) {
            // eslint-disable-next-line react/no-did-mount-set-state
            this.setState({
                roomAttributes: [],
                roomAvailability: {
                    bookableHours: [],
                    nonbookablePeriods: []
                },
                roomEquipment: {
                    availableEquipment: [],
                },
            });
        } else {
            const {roomId} = this.props;
            this.fetchRoomData(roomId);
        }
    }

    get newRoom() {
        const {roomId} = this.props;
        return roomId === null;
    }

    get loadingInitialData() {
        const {attributes, room, roomAttributes, roomEquipment, roomAvailability} = this.state;
        return !attributes || (!room && !this.newRoom) || !roomAttributes || !roomEquipment || !roomAvailability;
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

    async fetchRoomData(roomId) {
        const reqs = [
            this.fetchDetailedRoom(roomId),
            this.fetchRoomAttributes(roomId),
            this.fetchRoomAvailability(roomId),
            this.fetchRoomEquipment(roomId),
        ];
        this.setState(Object.assign(...await Promise.all(reqs)));
    }

    async fetchDetailedRoom(roomId) {
        let response;
        try {
            response = await indicoAxios.get(roomURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        return {room: camelizeKeys(response.data)};
    }

    async fetchRoomAttributes(roomId) {
        let response;
        try {
            response = await indicoAxios.get(fetchRoomAttributesURL({room_id: roomId}));
        } catch (error) {
            handleAxiosError(error);
            return;
        }
        return {roomAttributes: response.data};
    }

    async fetchRoomAvailability(roomId) {
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

    async fetchRoomEquipment(roomId) {
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
        const {
            afterCreation, onClose,
            actions: {fetchEquipmentTypes, fetchRoom, fetchRoomDetails, fetchRoomPermissions}
        } = this.props;
        const {wasEverSaved} = this.state;
        // eslint-disable-next-line react/destructuring-assignment
        const roomId = this.newRoom ? this.state.newRoomId : this.props.roomId;
        this.setState({closing: true});
        if (roomId !== null && wasEverSaved) {
            await Promise.all([
                fetchEquipmentTypes(),
                fetchRoom(roomId),
                fetchRoomPermissions(roomId),
                fetchRoomDetails(roomId, true)
            ]);
        }
        onClose(wasEverSaved || afterCreation);
    };

    handleSubmit = async (data, form) => {
        let {roomId} = this.props;
        const changedValues = getChangedValues(data, form);
        const basicDetailsKeys = ['attributes', 'bookableHours', 'nonbookablePeriods', 'availableEquipment'];
        const basicDetails = _.omit(changedValues, basicDetailsKeys);
        const {availableEquipment, nonbookablePeriods, bookableHours, attributes} = changedValues;
        let submitState = 'success';
        let submitError;
        try {
            if (this.newRoom) {
                roomId = await this.createRoom(basicDetails);
                this.setState({newRoomId: roomId});
            } else {
                await this.saveBasicDetails(roomId, basicDetails);
            }
            await this.saveEquipment(roomId, availableEquipment);
            await this.saveAttributes(roomId, attributes);
            await this.saveAvailability(roomId, changedValues, nonbookablePeriods, bookableHours);
        } catch (e) {
            submitError = handleSubmitError(e);
            submitState = 'error';
        }

        // reload room so the form gets new initialValues
        await this.fetchRoomData(roomId);
        this.setState({
            wasEverSaved: true,
            submitState,
        });
        return camelizeKeys(submitError);
    };

    async createRoom(basicDetails) {
        const {locationId} = this.props;
        const payload = snakifyKeys(basicDetails);
        payload.location_id = locationId;
        const response = await indicoAxios.post(roomsURL(), payload);
        return response.data.id;
    }

    async saveBasicDetails(roomId, basicDetails) {
        if (!_.isEmpty(basicDetails)) {
            await indicoAxios.patch(roomURL({room_id: roomId}), snakifyKeys(basicDetails));
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
            let params = snakifyKeys(_.pick(changedValues, ['bookableHours', 'nonbookablePeriods']));
            params = _.fromPairs(Object.entries(params).map(([field, values]) => [
                field, values.map(v => _.omit(v, 'key'))
            ]));
            await indicoAxios.post(updateRoomAvailabilityURL({room_id: roomId}), params);
        }
    }

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
                                    <FinalInput name={`${attribute}.value`}
                                                label={titles[fields.value[index].name]}
                                                required
                                                icon={{
                                                    name: 'remove',
                                                    color: 'red',
                                                    link: true,
                                                    onClick: () => fields.remove(index),
                                                }} />
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
        const {roomEquipment, room} = this.state;
        const {equipmentTypes, roomId} = this.props;
        const hasPhoto = this.newRoom ? false : room.hasPhoto;
        switch (content.type) {
            case 'header':
                if (content.key === 'photo' && this.newRoom) {
                    // XXX using the key for this is awful..
                    return null;
                }
                return (
                    <Header key={key}>{content.label}</Header>
                );
            case 'input': {
                return (
                    <FinalInput key={key}
                                name={content.name}
                                label={content.label}
                                required={content.required}
                                {...content.inputArgs} />
                );
            }
            case 'owner':
                return (
                    <FavoritesProvider key={key}>
                        {favoriteUsersController => (
                            <FinalPrincipal name={content.name}
                                            favoriteUsersController={favoriteUsersController}
                                            label={content.label}
                                            required
                                            allowNull />
                        )}
                    </FavoritesProvider>
                );
            case 'formgroup': {
                const {dependsOn} = content;
                const Wrapper = dependsOn ? FieldCondition : React.Fragment;
                const props = {key: content.key};

                if (dependsOn) {
                    props.when = dependsOn;
                }

                return (
                    <Wrapper {...props}>
                        {content.label && <Header as="h5">{content.label}</Header>}
                        <Form.Group widths="equal">
                            {content.content.map(this.renderContent)}
                        </Form.Group>
                    </Wrapper>
                );
            }

            case 'checkbox':
                return (
                    <FinalCheckbox key={key}
                                   name={content.name}
                                   label={content.label} />
                );
            case 'textarea':
                return (
                    <FinalTextArea key={key}
                                   name={content.name}
                                   label={content.label}
                                   parse={null} />
                );
            case 'emails':
                return (
                    <FinalEmailList key={key}
                                    name={content.name}
                                    label={content.label} />
                );
            case 'photo':
                return this.newRoom ? null : (
                    <RoomPhoto key={key} roomId={roomId} hasPhoto={hasPhoto} />
                );
            case 'attributes':
                return this.renderAttributes(content);
            case 'equipment':
                if (!roomEquipment && equipmentTypes) {
                    return;
                }
                return (
                    <FinalField key={key}
                                name="availableEquipment"
                                component={EquipmentList}
                                isEqual={_.isEqual}
                                componentLabel={Translate.string('Add new equipment')} />
                );
            case 'bookableHours':
                return (
                    <FinalField key={key}
                                name="bookableHours"
                                component={DailyAvailability}
                                isEqual={_.isEqual}
                                format={value => (value === null ? [] : value)} />
                );
            case 'nonBookablePeriods':
                return (
                    <FinalField key={key}
                                name="nonbookablePeriods"
                                component={NonBookablePeriods}
                                isEqual={_.isEqual}
                                format={value => (value === null ? [] : value)} />
                );
        }
    };

    renderModalContent = (fprops) => {
        const {afterCreation} = this.props;
        const {hasValidationErrors, pristine, submitting} = fprops;
        const {submitState, wasEverDirty} = this.state;
        return (
            <>
                <Modal.Header>
                    {this.newRoom ? Translate.string('Add Room') : Translate.string('Edit Room Details')}
                </Modal.Header>
                <Modal.Content scrolling>
                    <Form id="room-form"
                          styleName="room-form"
                          onSubmit={fprops.handleSubmit}>
                        <Grid columns={3}>
                            <Grid.Column>{columns[0].map(this.renderContent)}</Grid.Column>
                            <Grid.Column>{columns[1].map(this.renderContent)}</Grid.Column>
                            <Grid.Column>
                                {columns[2].map(this.renderContent)}
                                <Message styleName="submit-message" positive hidden={!afterCreation || wasEverDirty}>
                                    <Translate>
                                        Room has been successfully created.
                                    </Translate>
                                </Message>
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
                        {submitState === 'success' ? (
                            <Translate>Close</Translate>
                        ) : (
                            <Translate>Cancel</Translate>
                        )}
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
                                 this.setState({submitState: '', wasEverDirty: true});
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
        const {onClose} = this.props;
        const {room, roomAttributes, roomEquipment, roomAvailability, closing, newRoomId} = this.state;
        if (this.newRoom && newRoomId !== null) {
            // we just created a new room -> switch to the edit modal
            return <ConnectedRoomEditModal roomId={newRoomId} onClose={onClose} afterCreation />;
        }
        if (this.loadingInitialData || closing) {
            return <Dimmer active page><Loader /></Dimmer>;
        }
        const initialValues = this.newRoom ? {
            notificationEmails: [],
            notificationsEnabled: true,
            endNotificationsEnabled: true,
            isReservable: true,
            owner: null,
            reservationsNeedConfirmation: false,
            capacity: null,
            attributes: roomAttributes,
            ...roomEquipment,
            ...roomAvailability,
        } : {
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
                               initialValuesEqual={_.isEqual}
                               subscription={{submitting: true, hasValidationErrors: true, pristine: true}}
                               mutators={{...arrayMutators}} />
                </Modal>
            </>
        );
    }
}

const ConnectedRoomEditModal = connect(
    (state) => ({
        equipmentTypes: roomsSelectors.getAllEquipmentTypes(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            fetchEquipmentTypes: roomsActions.fetchEquipmentTypes,
            fetchRoom: roomsActions.fetchRoom,
            fetchRoomPermissions: userActions.fetchRoomPermissions,
            fetchRoomDetails: roomsActions.fetchDetails,
        }, dispatch),
    }),
)(RoomEditModal);


export default ConnectedRoomEditModal;
