// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Form, Button, Message, Input, Popup, Icon} from 'semantic-ui-react';

import {
  FinalEmailList,
  FinalTinyMCETextEditor,
  PlaceholderInfo,
  TinyMCETextEditor,
} from 'indico/react/components';
import {FinalCheckbox, FinalDropdown, FinalInput} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function RecipientsField({recipients}) {
  return (
    <Form.Field>
      <Translate as="label">Recipients</Translate>
      <Input
        value={recipients.join(', ')}
        readOnly
        icon={
          navigator.clipboard && (
            <Popup
              content={Translate.string('Copied!')}
              on="click"
              position="top center"
              inverted
              trigger={
                <Icon
                  name="copy"
                  color="black"
                  title={Translate.string('Copy to clipboard')}
                  onClick={() => navigator.clipboard.writeText(recipients.join(', '))}
                  link
                />
              }
            />
          )
        }
      />
    </Form.Field>
  );
}

RecipientsField.propTypes = {
  recipients: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export function EmailSentMessage({count}) {
  return (
    <Message positive>
      <PluralTranslate as={Message.Header} count={count}>
        <Singular>Your email has been sent.</Singular>
        <Plural>Your emails have been sent.</Plural>
      </PluralTranslate>
      <PluralTranslate count={count} as="p">
        <Singular>
          <Param name="count" value={count} /> email has been sent.
        </Singular>
        <Plural>
          <Param name="count" value={count} /> emails have been sent.
        </Plural>
      </PluralTranslate>
    </Message>
  );
}

EmailSentMessage.propTypes = {count: PropTypes.number.isRequired};

export function EmailDialog({
  onClose,
  onSubmit,
  senders,
  sentEmailsCount,
  previewURL,
  previewContext,
  placeholders,
  recipients,
  recipientsField,
  initialFormValues,
  validate,
}) {
  const [preview, setPreview] = useState(null);

  const togglePreview = async ({body, subject}) => {
    if (preview) {
      setPreview(undefined);
      return;
    }
    const {data} = await indicoAxios.post(previewURL, {body, subject, ...previewContext});
    setPreview(data);
  };

  const extraActions = (
    <Form.Field style={{marginRight: 'auto'}}>
      <FormSpy subscription={{values: true}}>
        {({values}) => (
          <Button type="button" active={!!preview} onClick={() => togglePreview(values)}>
            {!preview ? <Translate>Preview</Translate> : <Translate>Edit</Translate>}
          </Button>
        )}
      </FormSpy>
    </Form.Field>
  );

  const renderPreview = () => (
    <>
      <Message info>
        <Translate as={Message.Header}>
          This preview is only shown for a single recipient.
        </Translate>
        <Translate>
          When sending the emails, each recipient will receive an email customized with their
          personal data.
        </Translate>
      </Message>
      <Form.Field>
        <Translate as="label">Subject</Translate>
        {preview.subject}
      </Form.Field>
      <Form.Field>
        <Translate as="label">Email body</Translate>
        <TinyMCETextEditor
          value={preview.body}
          config={{showToolbar: false}}
          onChange={v => v}
          onFocus={v => v}
          onBlur={v => v}
          disabled
        />
      </Form.Field>
    </>
  );
  const form = (
    <>
      {preview && renderPreview()}
      <Form.Field style={{display: preview ? 'none' : 'block'}}>
        <FinalDropdown
          name="sender_address"
          label={Translate.string('Sender')}
          scrolling
          selection
          options={senders.map(([value, text]) => ({value, text}))}
          required
        />
        <FinalInput name="subject" label={Translate.string('Subject')} required maxLength={200} />
        <FinalTinyMCETextEditor
          name="body"
          label={Translate.string('Email body')}
          required
          config={{images: false, forceAbsoluteURLs: true}}
        />
        {placeholders.length > 0 && (
          <Form.Field>
            <PlaceholderInfo placeholders={placeholders} defaultOpen />
          </Form.Field>
        )}
        {recipientsField || <RecipientsField recipients={recipients} />}
        <FinalEmailList
          name="bcc_addresses"
          label={Translate.string('BCC addresses')}
          description={Translate.string('Send a copy of each email to every address in this list')}
        />
        <FinalCheckbox
          name="copy_for_sender"
          label={Translate.string('Send a copy of each email to my mailbox')}
          showAsToggle
        />
      </Form.Field>
    </>
  );

  return (
    <FinalModalForm
      id="send-email"
      size="standard"
      header={Translate.string('Send email')}
      initialValues={{
        sender_address: senders[0][0],
        subject: '',
        body: '',
        bcc_addresses: [],
        copy_for_sender: false,
        ...initialFormValues,
      }}
      initialValuesEqual={_.isEqual}
      onClose={onClose}
      onSubmit={onSubmit}
      submitLabel={Translate.string('Send')}
      extraActions={({submitSucceeded}) => !submitSucceeded && extraActions}
      disabledUntilChange={false}
      disabledAfterSubmit
      unloadPrompt
      scrolling
      validate={validate}
    >
      {({submitSucceeded}) =>
        submitSucceeded ? <EmailSentMessage count={sentEmailsCount} /> : form
      }
    </FinalModalForm>
  );
}

EmailDialog.propTypes = {
  onClose: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  senders: PropTypes.array.isRequired,
  sentEmailsCount: PropTypes.number,
  previewURL: PropTypes.string.isRequired,
  previewContext: PropTypes.object,
  placeholders: PropTypes.array.isRequired,
  /** Array of email addresses passed to <RecipientsField /> */
  recipients: PropTypes.arrayOf(PropTypes.string),
  /** React node to render instead of the default <RecipientsField /> component. */
  recipientsField: PropTypes.node,
  initialFormValues: PropTypes.object,
  validate: PropTypes.func,
};

EmailDialog.defaultProps = {
  previewContext: {},
  initialFormValues: {},
  sentEmailsCount: 0,
  recipients: [],
  recipientsField: null,
  validate: undefined,
};
