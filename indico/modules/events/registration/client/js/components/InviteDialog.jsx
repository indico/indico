// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import inviteImportURL from 'indico-url:event_registration.api_invitations_import';
import inviteMetadataURL from 'indico-url:event_registration.api_invitations_metadata';
import invitationPreviewURL from 'indico-url:event_registration.invitation_preview';
import inviteURL from 'indico-url:event_registration.invite';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useMemo, useState} from 'react';
import {Button, Dimmer, Form, Icon, Loader, Message, Segment} from 'semantic-ui-react';

import {EmailDialog} from 'indico/modules/events/persons/EmailDialog';
import {FinalPrincipalList} from 'indico/react/components/principals/PrincipalListField';
import {FinalCheckbox, FinalInput, handleSubmitError} from 'indico/react/forms';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {Translate, PluralTranslate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import ImportInvitationsField from './ImportInvitationsField';

function ExistingInviteFields({eventId}) {
  const favoriteUsersController = useFavoriteUsers();
  return (
    <FinalPrincipalList
      name="users"
      label={Translate.string('Users')}
      withExternalUsers
      eventId={eventId}
      favoriteUsersController={favoriteUsersController}
      required
    />
  );
}

ExistingInviteFields.propTypes = {
  eventId: PropTypes.number.isRequired,
};

function NewInviteFields() {
  return (
    <>
      <Form.Group widths="equal">
        <FinalInput name="first_name" label={Translate.string('First name')} required />
        <FinalInput name="last_name" label={Translate.string('Last name')} required />
      </Form.Group>
      <FinalInput
        name="email"
        type="email"
        label={Translate.string('Email')}
        required
        description={Translate.string('The invitation will be sent to this address.')}
      />
      <FinalInput name="affiliation" label={Translate.string('Affiliation')} />
    </>
  );
}

function ImportInviteFields({eventId, regformId}) {
  return (
    <>
      <Message info icon>
        <Icon name="lightbulb outline" />
        <Message.Content>
          <Translate as="p">
            You should upload a CSV (comma-separated values) file with exactly 4 columns in the
            following order:
          </Translate>
          <Message.List>
            <Translate as={Message.Item}>First Name</Translate>
            <Translate as={Message.Item}>Last Name</Translate>
            <Translate as={Message.Item}>Affiliation</Translate>
            <Translate as={Message.Item}>E-mail</Translate>
          </Message.List>
          <Translate as="p">
            The fields "First Name", "Last Name" and "E-mail" are mandatory.
          </Translate>
        </Message.Content>
      </Message>
      <ImportInvitationsField name="imported" eventId={eventId} regformId={regformId} />
      <FinalCheckbox
        name="skip_existing"
        label={Translate.string('Skip existing invitations')}
        description={Translate.string('Users with existing invitations will be ignored.')}
      />
    </>
  );
}

ImportInviteFields.propTypes = {
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
};

const modeConfig = {
  existing: {
    label: Translate.string('Indico users'),
    buttonLabel: Translate.string('Indico users'),
    renderFields: props => <ExistingInviteFields {...props} />,
    extraFields: ['users'],
    getPreviewPayload: ({users: [user] = []}) => ({context: {user}, disabled: !user}),
    getCount: ({users}) => users.length,
  },
  new: {
    label: Translate.string('New user'),
    buttonLabel: Translate.string('New user'),
    renderFields: () => <NewInviteFields />,
    extraFields: ['first_name', 'last_name', 'email', 'affiliation'],
    getPreviewPayload: values => {
      const firstName = values.first_name.trim();
      const lastName = values.last_name.trim();
      if (!firstName || !lastName) {
        return {context: {}, disabled: true};
      }
      return {context: {first_name: firstName, last_name: lastName}, disabled: false};
    },
    getCount: () => 1,
  },
  import: {
    label: Translate.string('Import CSV'),
    buttonLabel: Translate.string('Import CSV'),
    renderFields: props => <ImportInviteFields {...props} />,
    extraFields: ['imported', 'skip_existing'],
    getPreviewPayload: ({imported}) =>
      imported
        ? {
            context: _.pick(imported[0], ['first_name', 'last_name']),
            disabled: false,
          }
        : {context: {}, disabled: true},
    getCount: ({imported}) => imported.length,
  },
};

const getSkippedWarningMessage = skipped =>
  skipped
    ? PluralTranslate.string(
        '{count} invitation was skipped.',
        '{count} invitations were skipped.',
        skipped,
        {count: skipped}
      )
    : null;

export default function InviteDialog({eventId, regformId, onClose, onSuccess}) {
  const [mode, setMode] = useState('existing');
  const [sentEmailsCount, setSentEmailsCount] = useState(0);
  const [sentEmailsWarning, setSentEmailsWarning] = useState(null);
  const successTimeout = 5000;
  const {data: metadata, loading} = useIndicoAxios(
    inviteMetadataURL({event_id: eventId, reg_form_id: regformId}),
    {camelize: true}
  );

  const initialFormValues = useMemo(() => {
    if (!metadata) {
      return {};
    }
    return {
      subject: metadata.defaultSubject,
      body: metadata.defaultBody,
      skip_access_check: false,
      lock_email: false,
      skip_moderation: false,
      skip_existing: false,
      copy_for_sender: false,
      bcc_addresses: [],
      users: [],
      first_name: '',
      last_name: '',
      email: '',
      affiliation: '',
      imported: [],
    };
  }, [metadata]);

  const handleSubmit = useCallback(
    async values => {
      const count = modeConfig[mode].getCount(values);
      if (count === 0) {
        return {[modeConfig[mode].extraFields[0]]: 'No recipients specified.'};
      }
      const payload = _.pick(values, [
        'sender_address',
        'subject',
        'body',
        'bcc_addresses',
        'copy_for_sender',
        'skip_access_check',
        'lock_email',
        ...(metadata?.moderationEnabled ? ['skip_moderation'] : []),
        ...modeConfig[mode].extraFields,
      ]);

      const submitURL = mode === 'import' ? inviteImportURL : inviteURL;
      try {
        const {data} = await indicoAxios.post(
          submitURL({event_id: eventId, reg_form_id: regformId}),
          payload
        );
        onSuccess(data);
        setSentEmailsCount(data.sent);
        setSentEmailsWarning(getSkippedWarningMessage(data.skipped));
      } catch (error) {
        return handleSubmitError(error);
      }
      setTimeout(() => onClose(), successTimeout);
    },
    [eventId, metadata?.moderationEnabled, mode, onClose, onSuccess, regformId, successTimeout]
  );

  if (loading || !metadata) {
    return (
      <Dimmer active page inverted>
        <Loader />
      </Dimmer>
    );
  }

  const ModeFields = modeConfig[mode].renderFields;

  const recipientsField = (
    <>
      <Button.Group fluid attached="top">
        {['existing', 'new', 'import'].map(key => (
          <Button type="button" key={key} primary={mode === key} onClick={() => setMode(key)}>
            {modeConfig[key].buttonLabel}
          </Button>
        ))}
      </Button.Group>
      <Segment attached="bottom">
        <ModeFields eventId={eventId} regformId={regformId} />
      </Segment>
      {metadata.moderationEnabled && (
        <FinalCheckbox
          name="skip_moderation"
          label={Translate.string('Skip moderation')}
          description={Translate.string(
            "If enabled, the user's registration will be approved automatically."
          )}
        />
      )}
      <FinalCheckbox
        name="skip_access_check"
        label={Translate.string('Skip access check')}
        description={Translate.string(
          'If enabled, the user will be able to register even if the event is access-restricted.'
        )}
      />
      <FinalCheckbox
        name="lock_email"
        label={Translate.string('Lock email address')}
        description={Translate.string(
          'If enabled, the email address cannot be changed during registration.'
        )}
      />
    </>
  );

  return (
    <EmailDialog
      onSubmit={handleSubmit}
      onClose={onClose}
      senders={metadata.senders}
      placeholders={metadata.placeholders}
      previewURL={invitationPreviewURL({event_id: eventId, reg_form_id: regformId})}
      getPreviewPayload={values => modeConfig[mode].getPreviewPayload(values)}
      recipientsField={recipientsField}
      initialFormValues={initialFormValues}
      title={Translate.string('Invite people')}
      sentEmailsCount={sentEmailsCount}
      sentEmailsWarning={sentEmailsWarning}
      recipientsFirst
    />
  );
}

InviteDialog.propTypes = {
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  onSuccess: PropTypes.func.isRequired,
};
