// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailMetadataURL from 'indico-url:persons.api_email_event_persons_metadata';
import emailSendURL from 'indico-url:persons.api_email_event_persons_send';
import emailPreviewURL from 'indico-url:persons.email_event_persons_preview';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Form, Button, Message, Dimmer, Loader, Popup, Input, Icon} from 'semantic-ui-react';

import PlaceholderInfo from 'indico/react/components/PlaceholderInfo';
import TextEditor, {FinalTextEditor} from 'indico/react/components/TextEditor';
import {FinalCheckbox, FinalDropdown, FinalInput, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import './Email.module.scss';

const getIds = selector =>
  Array.from(document.querySelectorAll(selector))
    .filter(e => e.offsetWidth > 0 || e.offsetHeight > 0)
    .map(e => +e.value);

export function EmailButton({
  eventId,
  roleId,
  personSelector,
  userSelector,
  triggerSelector,
  extraParams,
}) {
  const [open, setOpen] = useState(false);
  const personIds = getIds(personSelector);
  const userIds = getIds(userSelector);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Translate as={Button} onClick={() => setOpen(true)}>
          Send email
        </Translate>
      )}
      {open && (
        <EmailForm
          eventId={eventId}
          personIds={personIds}
          userIds={userIds}
          roleIds={roleId && [roleId]}
          onClose={() => setOpen(false)}
          extraParams={extraParams}
        />
      )}
    </>
  );
}

EmailButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  roleId: PropTypes.number,
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  extraParams: PropTypes.object,
};

EmailButton.defaultProps = {
  roleId: undefined,
  personSelector: undefined,
  userSelector: undefined,
  triggerSelector: undefined,
  extraParams: undefined,
};

export function EmailForm({eventId, personIds, roleIds, userIds, onClose, extraParams}) {
  const [preview, setPreview] = useState(null);
  const recipientData = {personId: personIds, roleId: roleIds, userId: userIds, ...extraParams};
  const {data, loading} = useIndicoAxios({
    url: emailMetadataURL({event_id: eventId}),
    method: 'POST',
    data: snakifyKeys(recipientData),
  });
  const {
    senders = [],
    recipients = [],
    subject: defaultSubject,
    body: defaultBody,
    placeholders = [],
  } = data || {};
  const count = Object.values(recipientData).reduce((acc, v) => acc + v.length, 0);

  const togglePreview = async ({body, subject}) => {
    if (!preview) {
      body = body.getData ? body.getData() : body;
      const {data} = await indicoAxios.post(emailPreviewURL({event_id: eventId}), {body, subject});
      setPreview(data);
      return;
    }
    setPreview(undefined);
  };

  const onSubmit = async data => {
    const requestData = {...data, ...recipientData};
    requestData.body = requestData.body.getData ? requestData.body.getData() : requestData.body;
    try {
      await indicoAxios.post(emailSendURL({event_id: eventId}), snakifyKeys(requestData));
      setTimeout(() => onClose(), 5000);
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const extraActions = (
    <Form.Field styleName="preview-button">
      <FormSpy subscription={{values: true}}>
        {({values}) => (
          <Button type="button" active={!!preview} onClick={() => togglePreview(values)}>
            {!preview ? <Translate>Preview</Translate> : <Translate>Edit</Translate>}
          </Button>
        )}
      </FormSpy>
    </Form.Field>
  );

  const previewRender = preview && (
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
      <Form.Field required>
        <Translate as="label">Subject</Translate>
        {preview.subject}
      </Form.Field>
      <Form.Field required>
        <Translate as="label">Email body</Translate>
        <TextEditor
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

  const successMessage = (
    <Message positive>
      <Translate as={Message.Header}>Your email has been sent.</Translate>
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

  const form = (
    <>
      {previewRender}
      <Form.Field style={{display: preview ? 'none' : 'block'}}>
        <Form.Field>
          <FinalDropdown
            name="fromAddress"
            label={Translate.string('From')}
            scrolling
            selection
            options={senders.map(([value, text]) => ({value, text}))}
            required
          />
        </Form.Field>
        <Form.Field required>
          <Translate as="label">Subject</Translate>
          <FinalInput name="subject" required />
        </Form.Field>
        <Form.Field required>
          <Translate as="label">Email body</Translate>
          <FinalTextEditor name="body" required />
        </Form.Field>
        {placeholders.length > 0 && (
          <Form.Field>
            <PlaceholderInfo placeholders={placeholders} />
          </Form.Field>
        )}
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
        <Form.Field>
          <FinalCheckbox name="copyForSender" label={Translate.string('Send copy to me')} toggle />
          <Translate as="p" className="field-description">
            Send copy of each email to my mailbox
          </Translate>
        </Form.Field>
      </Form.Field>
    </>
  );

  return (
    <>
      <Dimmer active={loading} page inverted>
        <Loader />
      </Dimmer>
      {!loading && (
        <FinalModalForm
          id="send-email"
          size="standard"
          header={Translate.string('Send email')}
          initialValues={{
            fromAddress: senders[0][0],
            subject: defaultSubject,
            body: defaultBody,
          }}
          onClose={onClose}
          onSubmit={onSubmit}
          submitLabel={Translate.string('Send')}
          extraActions={({submitSucceeded}) => !submitSucceeded && extraActions}
          disabledUntilChange={false}
          disabledAfterSubmit
          unloadPrompt
        >
          {({submitSucceeded}) => (submitSucceeded ? successMessage : form)}
        </FinalModalForm>
      )}
    </>
  );
}

EmailForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  personIds: PropTypes.arrayOf(PropTypes.number),
  userIds: PropTypes.arrayOf(PropTypes.number),
  roleIds: PropTypes.arrayOf(PropTypes.number),
  onClose: PropTypes.func.isRequired,
  extraParams: PropTypes.object,
};

EmailForm.defaultProps = {
  personIds: [],
  userIds: [],
  roleIds: [],
  extraParams: {},
};
