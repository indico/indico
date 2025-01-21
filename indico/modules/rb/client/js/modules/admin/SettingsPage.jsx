// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Form, Header, Message, Placeholder} from 'semantic-ui-react';

import {FinalPrincipalList} from 'indico/react/components';
import {
  getChangedValues,
  FieldCondition,
  FinalCheckbox,
  FinalField,
  FinalInput,
  FinalSubmitButton,
  FinalUnloadPrompt,
  validators as v,
  FinalDropdown,
} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';
import {PluralTranslate, Translate} from 'indico/react/i18n';

import * as adminActions from './actions';
import CategoryList from './CategoryList';
import * as adminSelectors from './selectors';

import './SettingsPage.module.scss';

const SettingsPage = props => {
  const {
    settingsLoaded,
    settings,
    actions: {fetchSettings, updateSettings},
  } = props;

  const favoriteUsersController = useFavoriteUsers();
  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSubmit = async (data, form) => {
    const changedValues = getChangedValues(data, form);
    const rv = await updateSettings(changedValues);
    if (rv.error) {
      return rv.error;
    }
  };

  if (!settingsLoaded) {
    return (
      <Placeholder>
        <Placeholder.Line />
        <Placeholder.Line />
        <Placeholder.Line />
        <Placeholder.Line />
        <Placeholder.Line />
      </Placeholder>
    );
  }

  const bookingRequiredOptions = [
    {
      value: 'always',
      text: Translate.string('Always'),
    },
    {
      value: 'never',
      text: Translate.string('Never'),
    },
    {
      value: 'not_for_events',
      text: Translate.string('Not for events'),
    },
  ];

  return (
    <>
      <Header as="h2">
        <Translate>General Settings</Translate>
      </Header>
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={settings}
        initialValuesEqual={_.isEqual}
        subscription={{}}
      >
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <FinalUnloadPrompt />
            <Message>
              <Message.Header>
                <Translate>Specify who has access to the room booking system.</Translate>
              </Message.Header>
              <Form.Group widths="equal">
                <FinalPrincipalList
                  name="authorized_principals"
                  withGroups
                  favoriteUsersController={favoriteUsersController}
                  label={Translate.string('Authorized users')}
                  description={
                    <Translate>
                      Restrict access to the room booking system to these users/groups. If empty,
                      all logged-in users have access.
                    </Translate>
                  }
                />
                <FinalPrincipalList
                  name="admin_principals"
                  withGroups
                  favoriteUsersController={favoriteUsersController}
                  label={Translate.string('Administrators')}
                  description={
                    <Translate>
                      Grant full room booking admin permissions to these users/groups.
                    </Translate>
                  }
                />
              </Form.Group>
            </Message>
            <FinalCheckbox
              name="managers_edit_rooms"
              label={Translate.string('Allow owners/managers to edit their rooms')}
              description={
                <Translate>
                  By default only admins can modify rooms, but you can allow room owners and
                  managers to modify them as well.
                </Translate>
              }
            />
            <FinalCheckbox
              name="hide_booking_details"
              label={Translate.string('Hide booking details')}
              description={
                <Translate>
                  If enabled, only room managers and people involved in a booking can see details
                  such as who made the booking and its history.
                </Translate>
              }
            />
            <FinalCheckbox
              name="hide_module_if_unauthorized"
              label={Translate.string('Hide the Room Booking system from unauthorized users')}
              description={
                <Translate>
                  If enabled, links to the Room Booking system will not be shown to users who do not
                  have access to it.
                </Translate>
              }
            />
            <FinalInput
              name="tileserver_url"
              label={Translate.string('Tileserver URL')}
              description={
                <Translate>
                  If you want to use the map, specify the URL to a tileserver covering the area in
                  which your rooms are located.
                </Translate>
              }
              nullIfEmpty
              validate={val => {
                if (!val) {
                  return undefined;
                } else if (!val.match(/https?:\/\/.+/)) {
                  return Translate.string('Please provide a valid URL');
                } else {
                  const missing = ['{x}', '{y}', '{z}'].filter(x => !val.includes(x));
                  if (missing.length) {
                    return PluralTranslate.string(
                      'Missing placeholder: {placeholders}',
                      'Missing placeholders: {placeholders}',
                      missing.length,
                      {placeholders: missing.join(', ')}
                    );
                  }
                }
              }}
            />
            <FinalInput
              name="booking_limit"
              type="number"
              min="1"
              required
              label={Translate.string('Max. booking length')}
              description={Translate.string('The maximum length (in days) a booking may last.')}
              validate={v.min(1)}
            />
            <FinalDropdown
              options={bookingRequiredOptions}
              required
              selection
              name="booking_reason_required"
              label={Translate.string('Booking reason required')}
              description={Translate.string('Specify when a booking reason must be provided.')}
            />
            <FinalCheckbox
              name="notifications_enabled"
              label={Translate.string('Send reminders for upcoming bookings')}
            />
            <FieldCondition when="notifications_enabled">
              <Message>
                <Message.Header>
                  <Translate>
                    Specify how many days in advance booking reminders should be sent
                  </Translate>
                </Message.Header>
                <Form.Group widths="equal">
                  <FinalInput
                    name="notification_before_days"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Single/Daily bookings')}
                    validate={v.range(1, 30)}
                  />
                  <FinalInput
                    name="notification_before_days_weekly"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Weekly bookings')}
                    validate={v.range(1, 30)}
                  />
                  <FinalInput
                    name="notification_before_days_monthly"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Monthly bookings')}
                    validate={v.range(1, 30)}
                  />
                </Form.Group>
              </Message>
            </FieldCondition>
            <FinalCheckbox
              name="end_notifications_enabled"
              label={Translate.string('Send reminders when bookings are about to end')}
            />
            <FieldCondition when="end_notifications_enabled">
              <Message>
                <Message.Header>
                  <Translate>
                    Specify how many days before the end of a booking reminders should be sent
                  </Translate>
                </Message.Header>
                <Form.Group widths="equal">
                  <FinalInput
                    name="end_notification_daily"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Daily bookings')}
                    validate={v.range(1, 30)}
                  />
                  <FinalInput
                    name="end_notification_weekly"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Weekly bookings')}
                    validate={v.range(1, 30)}
                  />
                  <FinalInput
                    name="end_notification_monthly"
                    type="number"
                    min="1"
                    max="30"
                    required
                    label={Translate.string('Monthly bookings')}
                    validate={v.range(1, 30)}
                  />
                </Form.Group>
              </Message>
            </FieldCondition>
            <FinalCheckbox
              name="internal_notes_enabled"
              label={Translate.string('Enable internal booking notes')}
              description={
                <Translate>
                  Allow room owners/managers to add internal notes to bookings which are only
                  visible to other room owners/managers.
                </Translate>
              }
            />
            <FinalField
              name="excluded_categories"
              component={CategoryList}
              isEqual={_.isEqual}
              label={Translate.string('Disable booking during event creation')}
              description={
                <Translate>
                  Specify the IDs of categories for which booking a room during event creation will
                  not be suggested.
                </Translate>
              }
            />
            <FinalInput
              name="grace_period"
              type="number"
              min="0"
              max="24"
              validate={v.optional(v.range(0, 24))}
              label={Translate.string('Grace period')}
              description={
                <Translate>
                  Usually booking a space in the past is not allowed. This setting will allow to
                  book a room with a start date within a specified number of hours in the past.
                  Leaving the field empty will allow any start date that is not in the past without
                  restricting the start time as well.
                </Translate>
              }
            />
            <FinalSubmitButton
              label={Translate.string('Save')}
              style={{marginBottom: '0.875rem'}}
            />
          </Form>
        )}
      </FinalForm>
    </>
  );
};

SettingsPage.propTypes = {
  settingsLoaded: PropTypes.bool.isRequired,
  settings: PropTypes.object.isRequired,
  actions: PropTypes.exact({
    fetchSettings: PropTypes.func.isRequired,
    updateSettings: PropTypes.func.isRequired,
  }).isRequired,
};

export default connect(
  state => ({
    settings: adminSelectors.getSettings(state),
    settingsLoaded: adminSelectors.hasSettingsLoaded(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        fetchSettings: adminActions.fetchSettings,
        updateSettings: adminActions.updateSettings,
      },
      dispatch
    ),
  })
)(React.memo(SettingsPage));
