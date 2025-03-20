// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import attributesURL from 'indico-url:rb.admin_attributes';
import locationsURL from 'indico-url:rb.admin_locations';
import roomURL from 'indico-url:rb.admin_room';
import roomAttributesURL from 'indico-url:rb.admin_room_attributes';
import roomAvailabilityURL from 'indico-url:rb.admin_room_availability';
import roomsURL from 'indico-url:rb.admin_rooms';
import updateRoomAttributesURL from 'indico-url:rb.admin_update_room_attributes';
import updateRoomAvailabilityURL from 'indico-url:rb.admin_update_room_availability';
import updateRoomEquipmentURL from 'indico-url:rb.admin_update_room_equipment';
import roomNotificationDefaultsURL from 'indico-url:rb.notification_settings';
import roomPermissionInfoURL from 'indico-url:rb.room_permission_types';

import arrayMutators from 'final-form-arrays';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState, useCallback, useMemo} from 'react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Dimmer, Form, Grid, Loader, Menu, Message, Modal, Tab} from 'semantic-ui-react';

import {usePermissionInfo} from 'indico/react/components/principals/hooks';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import {actions as roomsActions} from '../../../common/rooms';
import {actions as userActions} from '../../../common/user';
import {getAllEquipmentTypes} from '../selectors';

import RoomEditDetails from './RoomEditDetails';
import RoomEditLocation from './RoomEditLocation';
import RoomEditNotifications from './RoomEditNotifications';
import RoomEditOptions from './RoomEditOptions';
import RoomEditPermissions from './RoomEditPermissions';
import RoomPhoto from './RoomPhoto';
import TabPaneError from './TabPaneError';

import './RoomEditModal.module.scss';

function RoomEditModal({roomId, locationId, onClose, afterCreation}) {
  const favoriteUsersController = useFavoriteUsers();
  const [permissionManager, permissionInfo] = usePermissionInfo(roomPermissionInfoURL());
  const equipmentTypes = useSelector(getAllEquipmentTypes);
  const dispatch = useDispatch();

  const {data: globalAttributes} = useIndicoAxios(attributesURL());
  const [newRoomId, setNewRoomId] = useState(null);
  const [wasEverUpdated, setWasEverUpdated] = useState(null);
  const [activeTab, setActiveTab] = useState('basic-details');
  const [loading, setLoading] = useState(false);

  const [roomDetails, setRoomDetails] = useState({
    acl_entries: [],
    available_equipment: [],
    notification_emails: [],
    notifications_enabled: true,
    end_notifications_enabled: true,
    is_reservable: true,
    reservations_need_confirmation: false,
    protection_mode: 'public',
    has_photo: false,
  });
  const [roomAttributes, setRoomAttributes] = useState([]);
  const [roomAvailability, setRoomAvailability] = useState({
    bookable_hours: [],
    nonbookable_periods: [],
  });
  const [roomNotificationDefaults, setRoomNotificationDefaults] = useState({});
  const [roomNameFormat, setRoomNameFormat] = useState('');

  const isNewRoom = roomId === undefined;

  const fetchData = async url => {
    let response;
    try {
      response = await indicoAxios.get(url);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    return response.data;
  };

  const fetchRoomData = useCallback(async () => {
    const resp = await Promise.all([
      fetchData(roomURL({room_id: roomId})),
      fetchData(roomAttributesURL({room_id: roomId})),
      fetchData(roomAvailabilityURL({room_id: roomId})),
      fetchData(roomNotificationDefaultsURL()),
    ]);
    [setRoomDetails, setRoomAttributes, setRoomAvailability, setRoomNotificationDefaults].forEach(
      (fn, i) => fn(resp[i])
    );
  }, [roomId]);

  const tabPanes = useMemo(
    () =>
      [
        {
          key: 'basic-details',
          menuItem: <Translate>Basic Details</Translate>,
          pane: (
            <RoomEditDetails
              key="basic-details"
              favoriteUsersController={favoriteUsersController}
            />
          ),
          fields: ['owner', 'key_location', 'telephone', 'capacity', 'division', 'comments'],
        },
        {
          key: 'location',
          menuItem: <Translate>Location</Translate>,
          pane: <RoomEditLocation key="location" roomNameFormat={roomNameFormat} />,
          fields: [
            'verbose_name',
            'site',
            'building',
            'floor',
            'number',
            'surface_area',
            'latitude',
            'longitude',
          ],
        },
        {
          key: 'permissions',
          menuItem: <Translate>Permissions</Translate>,
          pane: (
            <RoomEditPermissions
              key="permissions"
              permissionManager={permissionManager}
              permissionInfo={permissionInfo}
              favoriteUsersController={favoriteUsersController}
            />
          ),
          fields: ['protection_mode', 'acl_entries'],
        },
        {
          key: 'notifications',
          menuItem: <Translate>Notifications</Translate>,
          pane: <RoomEditNotifications key="notifications" defaults={roomNotificationDefaults} />,
          fields: [
            'notification_emails',
            'notifications_enabled',
            'end_notifications_enabled',
            'notification_before_days',
            'notification_before_days_weekly',
            'notification_before_days_monthly',
            'end_notification_daily',
            'end_notification_weekly',
            'end_notification_monthly',
          ],
        },
        {
          key: 'options',
          menuItem: <Translate>Options</Translate>,
          pane: (
            <RoomEditOptions
              key="options"
              showEquipment={!!equipmentTypes}
              globalAttributes={globalAttributes}
            />
          ),
          fields: [
            'bookable_hours',
            'nonbookable_periods',
            'available_equipment',
            'attributes',
            'is_reservable',
            'reservations_need_confirmation',
            'max_advance_days',
            'booking_limit_days',
          ],
        },
      ].map(pane => ({
        ...pane,
        menuItem: (
          <Menu.Item key={pane.key}>
            {pane.menuItem} {pane.key !== activeTab && <TabPaneError fields={pane.fields} />}
          </Menu.Item>
        ),
      })),
    [
      equipmentTypes,
      favoriteUsersController,
      globalAttributes,
      permissionInfo,
      permissionManager,
      activeTab,
      roomNotificationDefaults,
      roomNameFormat,
    ]
  );

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    const isAttributesDirty = form.getFieldState('attributes').dirty;
    const {
      attributes,
      bookable_hours: bookableHours,
      nonbookable_periods: nonbookablePeriods,
      available_equipment: availableEquipment,
      ...basicDetails
    } = changedValues;
    try {
      let response;
      if (isNewRoom) {
        const payload = {...basicDetails};
        payload.location_id = locationId;
        response = await indicoAxios.post(roomsURL(), payload);
      } else if (!_.isEmpty(basicDetails)) {
        await indicoAxios.patch(roomURL({room_id: roomId}), basicDetails);
      }
      const roomIdArgs = {room_id: isNewRoom ? response.data.id : roomId};
      if (availableEquipment) {
        await indicoAxios.post(updateRoomEquipmentURL(roomIdArgs), {
          available_equipment: availableEquipment,
        });
      }
      if (isAttributesDirty) {
        await indicoAxios.post(updateRoomAttributesURL(roomIdArgs), {attributes: attributes || []});
      }
      if (bookableHours || nonbookablePeriods) {
        const availability = {bookableHours, nonbookablePeriods};
        await indicoAxios.post(updateRoomAvailabilityURL(roomIdArgs), snakifyKeys(availability));
      }
      // reload room so the form gets new initialValues
      if (!isNewRoom) {
        setWasEverUpdated(true);
        fetchRoomData();
      } else {
        setNewRoomId(response.data.id);
      }
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const closeModal = useCallback(async () => {
    setLoading(true);
    if ((roomId || newRoomId) !== null && wasEverUpdated) {
      await Promise.all([
        dispatch(roomsActions.fetchRoom(roomId)),
        dispatch(roomsActions.fetchEquipmentTypes()),
        dispatch(roomsActions.fetchDetails(roomId, true)),
        dispatch(userActions.fetchRoomPermissions(roomId)),
      ]);
    }
    onClose(wasEverUpdated || afterCreation);
  }, [dispatch, onClose, roomId, newRoomId, wasEverUpdated, afterCreation]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      if (!isNewRoom) {
        fetchRoomData().then(() => setLoading(false));
      }

      const location = await fetchData(locationsURL({location_id: locationId}));
      setRoomNameFormat(location.room_name_format);
      setLoading(false);
    })();
  }, [isNewRoom, fetchRoomData, locationId]);

  const formValidation = values => {
    if (!!values.latitude !== !!values.longitude) {
      // Validation for dependent fields is made at the form level, since field
      // level won't handle it properly.
      const error = Translate.string('Both latitude and longitude need to be set (or omitted).');
      return {latitude: error, longitude: error};
    }
  };

  const renderModal = formProps => {
    const {
      handleSubmit: handleFormSubmit,
      hasValidationErrors,
      pristine,
      submitting,
      dirty,
    } = formProps;
    if (loading) {
      return (
        <Dimmer active page>
          <Loader />
        </Dimmer>
      );
    }
    return (
      <Modal open onClose={closeModal} size="large" centered={false} closeIcon>
        <Modal.Header>
          {isNewRoom ? <Translate>Add Room</Translate> : <Translate>Edit Room Details</Translate>}
        </Modal.Header>
        <Modal.Content>
          <Message styleName="submit-message" positive hidden={!afterCreation || wasEverUpdated}>
            <Translate>Room has been successfully created.</Translate>
          </Message>
          <FormSpy subscription={{submitSucceeded: true, modifiedSinceLastSubmit: true}}>
            {({submitSucceeded, modifiedSinceLastSubmit}) => {
              return (
                <Message
                  styleName="submit-message"
                  positive
                  hidden={!submitSucceeded || modifiedSinceLastSubmit}
                >
                  <Translate>Room has been successfully updated.</Translate>
                </Message>
              );
            }}
          </FormSpy>
          <FormSpy subscription={{submitFailed: true}}>
            {({submitFailed}) => {
              return (
                <Message styleName="submit-message" negative hidden={!submitFailed || dirty}>
                  <p>
                    <Translate>Room could not be updated.</Translate>
                  </p>
                  <Button
                    type="button"
                    icon="undo"
                    size="mini"
                    color="red"
                    content={Translate.string('Reset form')}
                    onClick={() => formProps.form.reset()}
                  />
                </Message>
              );
            }}
          </FormSpy>
          <Grid columns="equal">
            {!isNewRoom && (
              <Grid.Column width={4}>
                <RoomPhoto roomId={roomId} hasPhoto={roomDetails && roomDetails.has_photo} />
              </Grid.Column>
            )}
            <Grid.Column>
              <Form id="room-form" onSubmit={handleFormSubmit}>
                <Tab
                  renderActiveOnly={false}
                  panes={tabPanes}
                  onTabChange={(__, {activeIndex}) => {
                    setActiveTab(tabPanes[activeIndex].key);
                  }}
                />
              </Form>
            </Grid.Column>
          </Grid>
        </Modal.Content>
        <Modal.Actions>
          <FormSpy subscription={{submitSucceeded: true}}>
            {({submitSucceeded}) => (
              <Button onClick={closeModal}>
                {submitSucceeded ? <Translate>Close</Translate> : <Translate>Cancel</Translate>}
              </Button>
            )}
          </FormSpy>
          <Button
            type="submit"
            form="room-form"
            disabled={pristine || submitting || hasValidationErrors}
            loading={submitting}
            primary
          >
            <Translate>Save</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
    );
  };

  if (newRoomId) {
    return (
      <RoomEditModal roomId={newRoomId} locationId={locationId} onClose={onClose} afterCreation />
    );
  }
  if (!roomDetails || !roomAvailability || !roomAttributes) {
    // In case of error, nothing is returned
    return null;
  }

  return (
    <FinalForm
      onSubmit={handleSubmit}
      initialValues={{
        ...roomDetails,
        ...roomAvailability,
        attributes: roomAttributes,
      }}
      initialValuesEqual={_.isEqual}
      render={renderModal}
      subscription={{
        submitting: true,
        hasValidationErrors: true,
        pristine: true,
        dirty: true,
      }}
      mutators={{...arrayMutators}}
      validate={formValidation}
    />
  );
}

RoomEditModal.propTypes = {
  roomId: PropTypes.number,
  locationId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  afterCreation: PropTypes.bool,
};

RoomEditModal.defaultProps = {
  roomId: undefined,
  afterCreation: false,
};

export default RoomEditModal;
