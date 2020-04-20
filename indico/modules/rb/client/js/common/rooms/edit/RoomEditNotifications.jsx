// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import PropTypes from 'prop-types';
import {Translate} from 'indico/react/i18n';
import {FieldCondition, FinalInput, validators as v} from 'indico/react/forms';
import {FinalEmailList} from 'indico/react/components';

function RoomEditNotifications({active}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Notifications</Translate>
      </Header>
      <FinalEmailList
        name="notification_emails"
        label={Translate.string('Notification emails')}
        hideErrorPopup={!active}
      />
      <FieldCondition when="notifications_enabled">
        <Header as="h5">
          <Translate>How many days in advance booking reminders should be sent</Translate>
        </Header>
        <Form.Group widths="equal">
          <FinalInput
            fluid
            name="notification_before_days"
            label={Translate.string('Single/Daily')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="notification_before_days_weekly"
            label={Translate.string('Weekly')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="notification_before_days_monthly"
            label={Translate.string('Monthly')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
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
            label={Translate.string('Daily')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="end_notification_weekly"
            label={Translate.string('Weekly')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="end_notification_monthly"
            label={Translate.string('Monthly')}
            type="number"
            validate={v.optional(v.range(1, 30))}
            hideErrorPopup={!active}
          />
        </Form.Group>
      </FieldCondition>
    </Tab.Pane>
  );
}

RoomEditNotifications.propTypes = {
  active: PropTypes.bool,
};

RoomEditNotifications.defaultProps = {
  active: true,
};

export default RoomEditNotifications;
