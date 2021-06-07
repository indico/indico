// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Header, Tab} from 'semantic-ui-react';

import {FinalEmailList} from 'indico/react/components';
import {FieldCondition, FinalCheckbox, FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function RoomEditNotifications({active, roomNotificationSettings}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Notifications</Translate>
      </Header>
      <FinalEmailList name="notification_emails" label={Translate.string('Notification emails')} />
      <Form.Group grouped>
        <FinalCheckbox name="notifications_enabled" label={Translate.string('Reminders enabled')} />
        <FinalCheckbox
          name="end_notifications_enabled"
          label={Translate.string('Reminders of finishing bookings enabled')}
        />
      </Form.Group>
      <FieldCondition when="notifications_enabled">
        <Header as="h5">
          <Translate>How many days in advance booking reminders should be sent</Translate>
        </Header>
        <Form.Group widths="equal">
          <FinalInput
            fluid
            name="notification_before_days"
            placeholder={roomNotificationSettings.notification_before_days}
            label={Translate.string('Single/Daily')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="notification_before_days_weekly"
            placeholder={roomNotificationSettings.notification_before_days_weekly}
            label={Translate.string('Weekly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="notification_before_days_monthly"
            placeholder={roomNotificationSettings.notification_before_days_monthly}
            label={Translate.string('Monthly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
        </Form.Group>
      </FieldCondition>
      <FieldCondition when="end_notifications_enabled">
        <Header as="h5">
          <Translate>How many days before the end of a booking should reminders be sent</Translate>
        </Header>
        <Form.Group widths="equal">
          <FinalInput
            fluid
            name="end_notification_daily"
            placeholder={roomNotificationSettings.end_notification_daily}
            label={Translate.string('Daily')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="end_notification_weekly"
            placeholder={roomNotificationSettings.end_notification_weekly}
            label={Translate.string('Weekly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="end_notification_monthly"
            placeholder={roomNotificationSettings.end_notification_monthly}
            label={Translate.string('Monthly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
        </Form.Group>
      </FieldCondition>
    </Tab.Pane>
  );
}

RoomEditNotifications.propTypes = {
  active: PropTypes.bool,
  roomNotificationSettings: PropTypes.shape({
    notification_before_days: PropTypes.string,
    notification_before_days_weekly: PropTypes.string,
    notification_before_days_monthly: PropTypes.string,
    end_notification_daily: PropTypes.string,
    end_notification_weekly: PropTypes.string,
    end_notification_monthly: PropTypes.string,
  }),
};

RoomEditNotifications.defaultProps = {
  active: true,
  roomNotificationSettings: PropTypes.shape({
    notification_before_days: '',
    notification_before_days_weekly: '',
    notification_before_days_monthly: '',
    end_notification_daily: '',
    end_notification_weekly: '',
    end_notification_monthly: '',
  }),
};
