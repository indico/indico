// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

export default function RoomEditNotifications({active, defaults}) {
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
            placeholder={
              defaults.notification_before_days && String(defaults.notification_before_days)
            }
            label={Translate.string('Single/Daily')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="notification_before_days_weekly"
            placeholder={
              defaults.notification_before_days_weekly &&
              String(defaults.notification_before_days_weekly)
            }
            label={Translate.string('Weekly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="notification_before_days_monthly"
            placeholder={
              defaults.notification_before_days_monthly &&
              String(defaults.notification_before_days_monthly)
            }
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
            placeholder={defaults.end_notification_daily && String(defaults.end_notification_daily)}
            label={Translate.string('Daily')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="end_notification_weekly"
            placeholder={
              defaults.end_notification_weekly && String(defaults.end_notification_weekly)
            }
            label={Translate.string('Weekly')}
            type="number"
            min="1"
            max="30"
            validate={v.optional(v.range(1, 30))}
          />
          <FinalInput
            fluid
            name="end_notification_monthly"
            placeholder={
              defaults.end_notification_monthly && String(defaults.end_notification_monthly)
            }
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
  defaults: PropTypes.shape({
    notification_before_days: PropTypes.number,
    notification_before_days_weekly: PropTypes.number,
    notification_before_days_monthly: PropTypes.number,
    end_notification_daily: PropTypes.number,
    end_notification_weekly: PropTypes.number,
    end_notification_monthly: PropTypes.number,
  }),
};

RoomEditNotifications.defaultProps = {
  active: true,
  defaults: PropTypes.shape({
    notification_before_days: null,
    notification_before_days_weekly: null,
    notification_before_days_monthly: null,
    end_notification_daily: null,
    end_notification_weekly: null,
    end_notification_monthly: null,
  }),
};
