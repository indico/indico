// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailAttributesURL from 'indico-url:persons.email_event_persons';
import emailPreviewURL from 'indico-url:persons.email_event_persons_preview';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Form, Button, TextArea, Message, Dimmer, Loader} from 'semantic-ui-react';

import PlaceholderInfo from 'indico/react/components/PlaceholderInfo';
import TextEditor, {FinalTextEditor} from 'indico/react/components/TextEditor';
import {FinalCheckbox, FinalDropdown, FinalInput, handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import './Email.module.scss';

const useIdSelector = selector =>
  Array.from(document.querySelectorAll(selector))
    .filter(e => e.offsetWidth > 0 || e.offsetHeight > 0)
    .map(e => +e.value);

// TODO: use existing button
// TODO: disable if none selected
export function EmailButton({
  eventId,
  roleId,
  personSelector,
  userSelector,
  triggerSelector,
  trigger,
  extraParams,
}) {
  const [open, setOpen] = useState(false);
  const personIds = useIdSelector(personSelector);
  const userIds = useIdSelector(userSelector);

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
      {!triggerSelector && !trigger && (
        <Translate as={Button} onClick={() => setOpen(true)}>
          Send email
        </Translate>
      )}
      {open && (
        <EmailForm
          eventId={eventId}
          personIds={personIds}
          userIds={userIds}
          roleIds={[roleId]}
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
  trigger: PropTypes.node,
  extraParams: PropTypes.object,
};

EmailButton.defaultProps = {
  roleId: undefined,
  personSelector: undefined,
  userSelector: undefined,
  triggerSelector: undefined,
  trigger: undefined,
  extraParams: undefined,
};

export function EmailForm({eventId, personIds, roleIds, userIds, onClose, extraParams}) {
  const [preview, setPreview] = useState(null);
  const recipientData = {personId: personIds, roleId: roleIds, userId: userIds, ...extraParams};
  const {data, loading} = useIndicoAxios({
    url: emailAttributesURL({event_id: eventId}),
    params: snakifyKeys(recipientData),
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
      const {data} = await indicoAxios.post(emailPreviewURL({event_id: eventId}), {body, subject});
      setPreview(data);
      return;
    }
    setPreview(undefined);
  };

  const onSubmit = async data => {
    try {
      await indicoAxios.post(emailAttributesURL({event_id: eventId}), snakifyKeys(data), {
        params: snakifyKeys(recipientData),
      });
      onClose(); // TODO display success message
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const extraActions = (
    <Form.Field>
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

  const form = fprops => (
    <>
      {fprops.submitSucceeded && (
        <Message positive>
          <Translate as={Message.Header}>Your email has been sent.</Translate>
          <PluralTranslate count={count} as="p">
            <Singular>One email has been sent.</Singular>
            <Plural>
              <Param name="count" value={count} /> emails have been sent.
            </Plural>
          </PluralTranslate>
        </Message>
      )}
      {preview && (
        <Message info>
          <Translate as={Message.Header}>
            This preview is only shown for a single recipient.
          </Translate>
          <Translate>
            When sending the emails, each recipient will receive an email customized with their
            personal data.
          </Translate>
        </Message>
      )}
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
      <Form.Field style={{display: preview ? 'none' : 'block'}}>
        <Form.Field required>
          <Translate as="label">Subject</Translate>
          <FinalInput name="subject" required />
        </Form.Field>
        <Form.Field required>
          <Translate as="label">Email body</Translate>
          <FinalTextEditor name="body" required />
        </Form.Field>
        {placeholders.length > 0 && <PlaceholderInfo placeholders={placeholders} />}
      </Form.Field>
      {previewRender}
      <Form.Field>
        <Translate as="label">Recipients</Translate>
        <TextArea rows={3} value={recipients.join(', ')} readOnly />
      </Form.Field>
      <Form.Field>
        <FinalCheckbox name="copyForSender" label={Translate.string('Send copy to me')} toggle />
        <Translate as="p" className="field-description">
          Send copy of each email to my mailbox
        </Translate>
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
          size="small"
          header={Translate.string('Send email')}
          initialValues={{
            fromAddress: senders[0][0],
            subject: defaultSubject,
            body: defaultBody,
          }}
          onClose={onClose}
          onSubmit={onSubmit}
          submitLabel={Translate.string('Send')}
          extraActions={extraActions}
          disabledUntilChange={false}
          unloadPrompt
        >
          {form}
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
