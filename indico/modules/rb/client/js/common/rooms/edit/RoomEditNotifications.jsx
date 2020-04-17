import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import PropTypes from 'prop-types';
import {Translate} from 'indico/react/i18n';
import {FieldCondition, FinalInput} from 'indico/react/forms';
import {FinalEmailList} from 'indico/react/components';

function RoomEditNotifications({active}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Notifications</Translate>
      </Header>
      <FinalEmailList
        name="notificationEmails"
        label={Translate.string('Notification emails')}
        hideErrorPopup={!active}
      />
      <FieldCondition when="notificationsEnabled">
        <Header as="h5">
          <Translate>How many days in advance booking reminders should be sent</Translate>
        </Header>
        <Form.Group widths="equal">
          <FinalInput
            fluid
            name="notificationBeforeDays"
            label={Translate.string('Single/Daily')}
            type="number"
            min={1}
            max={30}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="notificationBeforeDaysWeekly"
            label={Translate.string('Weekly')}
            type="number"
            min={1}
            max={30}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="notificationBeforeDaysMonthly"
            label={Translate.string('Monthly')}
            type="number"
            min={1}
            max={30}
            hideErrorPopup={!active}
          />
        </Form.Group>
      </FieldCondition>
      <FieldCondition when="endNotificationsEnabled">
        <Header as="h5">
          <Translate>How many days before the end of a booking should reminders be sent</Translate>
        </Header>
        <Form.Group widths="equal">
          <FinalInput
            fluid
            name="endNotificationDaily"
            label={Translate.string('Daily')}
            type="number"
            min={1}
            max={30}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="endNotificationWeekly"
            label={Translate.string('Weekly')}
            type="number"
            min={1}
            max={30}
            hideErrorPopup={!active}
          />
          <FinalInput
            fluid
            name="endNotificationMonthly"
            label={Translate.string('Monthly')}
            type="number"
            min={1}
            max={30}
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
