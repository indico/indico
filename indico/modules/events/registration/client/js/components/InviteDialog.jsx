// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import inviteImportURL from 'indico-url:event_registration.api_invitations_import';
import inviteImportUploadURL from 'indico-url:event_registration.api_invitations_import_upload';
import inviteMetadataURL from 'indico-url:event_registration.api_invitations_metadata';
import invitationPreviewURL from 'indico-url:event_registration.invitation_preview';
import inviteURL from 'indico-url:event_registration.invite';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Field} from 'react-final-form';
import {Button, Dimmer, Form, Icon, Loader, Message, Popup, Segment} from 'semantic-ui-react';

import {EmailDialog} from 'indico/modules/events/persons/EmailDialog';
import {FinalSingleFileManager} from 'indico/react/components';
import {FinalPrincipalList} from 'indico/react/components/principals/PrincipalListField';
import {FinalCheckbox, FinalDropdown, FinalInput, handleSubmitError} from 'indico/react/forms';
import {useFavoriteUsers, useIndicoAxios} from 'indico/react/hooks';
import {Translate, PluralTranslate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function ExistingInviteFields({eventId, favoriteUsersController, onPrincipalsResolved}) {
  return (
    <FinalPrincipalList
      name="users"
      label={Translate.string('Users')}
      withExternalUsers
      eventId={eventId}
      favoriteUsersController={favoriteUsersController}
      onPrincipalsResolved={onPrincipalsResolved}
      required
    />
  );
}

ExistingInviteFields.propTypes = {
  eventId: PropTypes.number.isRequired,
  favoriteUsersController: PropTypes.array.isRequired,
  onPrincipalsResolved: PropTypes.func.isRequired,
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

function ImportInviteFields({csvDelimiterOptions, eventId, regformId}) {
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
      <Field name="source_file" subscription={{value: true}}>
        {({input: {value: sourceFile}}) => (
          <Popup
            content={Translate.string('Remove the uploaded CSV before changing the delimiter.')}
            disabled={!sourceFile}
            trigger={
              <div>
                <FinalDropdown
                  name="delimiter"
                  label={Translate.string('CSV delimiter')}
                  selection
                  required
                  options={csvDelimiterOptions}
                  disabled={!!sourceFile}
                  placeholder={Translate.string('Select delimiter')}
                />
              </div>
            }
          />
        )}
      </Field>
      <Field name="delimiter" subscription={{value: true}}>
        {({input: {value: delimiter}}) => {
          const uploadURL = inviteImportUploadURL({
            event_id: eventId,
            reg_form_id: regformId,
            delimiter,
          });
          return (
            <FinalSingleFileManager
              name="source_file"
              uploadURL={uploadURL}
              validExtensions={['csv']}
              required
            />
          );
        }}
      </Field>
      <FinalCheckbox
        name="skip_existing"
        label={Translate.string('Skip existing invitations')}
        description={Translate.string('Users with existing invitations will be ignored.')}
      />
    </>
  );
}

ImportInviteFields.propTypes = {
  csvDelimiterOptions: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
    })
  ).isRequired,
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
};

const modeConfig = {
  existing: {
    label: Translate.string('Indico users'),
    buttonLabel: Translate.string('Indico users'),
    renderFields: props => <ExistingInviteFields {...props} />,
    extraFields: ['users'],
    getPreviewPayload: (values, resolvedPrincipals) => {
      if (!resolvedPrincipals.length) {
        return {context: {}, disabled: true};
      }
      const {firstName, lastName} = resolvedPrincipals[0];
      return {context: {first_name: firstName, last_name: lastName}, disabled: false};
    },
  },
  new: {
    label: Translate.string('New user'),
    buttonLabel: Translate.string('New user'),
    renderFields: () => <NewInviteFields />,
    extraFields: ['first_name', 'last_name', 'email', 'affiliation'],
    getPreviewPayload: values => {
      const firstName = values.first_name?.trim();
      const lastName = values.last_name?.trim();
      if (!firstName || !lastName) {
        return {context: {}, disabled: true};
      }
      return {context: {first_name: firstName, last_name: lastName}, disabled: false};
    },
  },
  import: {
    label: Translate.string('Import CSV'),
    buttonLabel: Translate.string('Import CSV'),
    renderFields: props => <ImportInviteFields {...props} />,
    extraFields: ['source_file', 'skip_existing'],
    getPreviewPayload: values => {
      const sourceFile = values.source_file;
      if (!sourceFile) {
        return {context: {}, disabled: true};
      }

      return {
        context: {source_file: sourceFile},
        disabled: false,
      };
    },
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
  const favoriteUsersController = useFavoriteUsers();
  const [mode, setMode] = useState('existing');
  const [resolvedPrincipals, setResolvedPrincipals] = useState([]);
  const [sentEmailsCount, setSentEmailsCount] = useState(0);
  const [sentEmailsWarning, setSentEmailsWarning] = useState(null);
  const successTimeout = 5000;
  const {data: metadata, loading} = useIndicoAxios(
    inviteMetadataURL({event_id: eventId, reg_form_id: regformId}),
    {camelize: true}
  );

  useEffect(() => {
    if (mode === 'new') {
      setResolvedPrincipals([]);
    }
  }, [mode]);

  const csvDelimiterOptions = useMemo(() => {
    return (metadata?.csvDelimiters || []).map(d => ({value: d.value, text: d.text}));
  }, [metadata]);

  const defaultDelimiter = metadata?.defaultDelimiter || csvDelimiterOptions[0]?.value || '';

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
      source_file: null,
      delimiter: defaultDelimiter,
    };
  }, [metadata, defaultDelimiter]);

  const handlePrincipalsResolved = useCallback(entries => {
    setResolvedPrincipals(prev => (_.isEqual(prev, entries) ? prev : entries));
  }, []);

  const handleSubmit = useCallback(
    async values => {
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

      if (mode === 'import') {
        if (!values.source_file) {
          return {source_file: Translate.string('Please upload a CSV file.')};
        }
        try {
          const {data} = await indicoAxios.post(
            inviteImportURL({event_id: eventId, reg_form_id: regformId}),
            payload
          );
          onSuccess(data);
          setSentEmailsCount(data.sent ?? 0);
          setSentEmailsWarning(getSkippedWarningMessage(data.skipped ?? 0));
          setTimeout(() => onClose(), successTimeout);
        } catch (error) {
          return handleSubmitError(error);
        }
        return;
      }

      if (mode === 'existing' && !payload.users.length) {
        return {users: Translate.string('Select at least one user.')};
      }

      try {
        const targetURL = inviteURL({
          event_id: eventId,
          reg_form_id: regformId,
          existing: mode === 'new' ? 0 : 1,
        });
        const response = await indicoAxios.post(targetURL, payload);
        onSuccess(response.data);
        setSentEmailsCount(response.data.sent ?? 0);
        setSentEmailsWarning(getSkippedWarningMessage(response.data.skipped ?? 0));
        setTimeout(() => onClose(), successTimeout);
      } catch (error) {
        return handleSubmitError(error);
      }
      return;
    },
    [eventId, metadata?.moderationEnabled, mode, onClose, onSuccess, regformId, successTimeout]
  );

  const getPreviewPayload = useCallback(
    values => modeConfig[mode].getPreviewPayload(values, resolvedPrincipals),
    [mode, resolvedPrincipals]
  );

  const modeProps = useMemo(() => {
    switch (mode) {
      case 'existing':
        return {eventId, favoriteUsersController, onPrincipalsResolved: handlePrincipalsResolved};
      case 'import':
        return {
          csvDelimiterOptions,
          eventId,
          regformId,
        };
      default:
        return {};
    }
  }, [
    csvDelimiterOptions,
    eventId,
    favoriteUsersController,
    handlePrincipalsResolved,
    mode,
    regformId,
  ]);

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
        <ModeFields {...modeProps} />
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
      getPreviewPayload={getPreviewPayload}
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
