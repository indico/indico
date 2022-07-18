// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailAttributesURL from 'indico-url:persons.email_event_persons';
import emailPreviewURL from 'indico-url:persons.email_event_persons_preview';

import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {Form as FinalForm, FormSpy} from 'react-final-form';
import {Form, Modal, Button, TextArea, Message, Input, Label} from 'semantic-ui-react';

import TextEditor from 'indico/react/components/TextEditor';
import {
  FinalCheckbox,
  FinalDropdown,
  FinalField,
  FinalInput,
  handleSubmitError,
  validators,
} from 'indico/react/forms';
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
  personSelector,
  userSelector,
  roleSelector,
  triggerSelector,
  trigger,
}) {
  const [open, setOpen] = useState(false);
  const personIds = useIdSelector(personSelector);
  const userIds = useIdSelector(userSelector);
  const roleIds = useIdSelector(roleSelector);

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
    <Modal
      onClose={() => setOpen(false)}
      onOpen={() => setOpen(true)}
      open={open}
      trigger={
        !triggerSelector ? trigger || <Translate as={Button}>Send email</Translate> : undefined
      }
      closeIcon
    >
      <Translate as={Modal.Header}>Send email</Translate>
      <Modal.Content>
        <EmailForm eventId={eventId} personIds={personIds} userIds={userIds} roleIds={roleIds} />
      </Modal.Content>
    </Modal>
  );
}

EmailButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  roleSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  trigger: PropTypes.node,
};

EmailButton.defaultProps = {
  personSelector: undefined,
  userSelector: undefined,
  roleSelector: undefined,
  triggerSelector: undefined,
  trigger: undefined,
};

export function EmailForm({eventId, personIds, roleIds, userIds}) {
  const [preview, setPreview] = useState(null);
  // Prevents CKEditor5 onChange call when the editor data is updated in preview
  const disableChange = useRef(false);
  const recipientData = {personId: personIds, roleId: roleIds, userId: userIds};
  const {data, loading} = useIndicoAxios({
    url: emailAttributesURL({event_id: eventId}),
    params: snakifyKeys(recipientData),
  });
  const {senders = [], recipients = [], subject: defaultSubject, body: defaultBody} = data || {};
  const count = Object.values(recipientData).reduce((acc, v) => acc + v.length, 0);

  const togglePreview = async ({body, subject}) => {
    if (!preview) {
      const {data} = await indicoAxios.post(emailPreviewURL({event_id: eventId}), {body, subject});
      disableChange.current = true;
      setPreview(data);
      return;
    }
    disableChange.current = false;
    setPreview(undefined);
  };

  const onSubmit = async data => {
    try {
      await indicoAxios.post(emailAttributesURL({event_id: eventId}), snakifyKeys(data), {
        params: snakifyKeys(recipientData),
      });
    } catch (err) {
      return handleSubmitError(err);
    }
  };

  const renderForm = ({handleSubmit, submitting, submitSucceeded, hasValidationErrors}) => (
    <Form loading={loading} onSubmit={handleSubmit}>
      {submitSucceeded && (
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
        {preview ? (
          <Input value={preview.subject} disabled required />
        ) : (
          <FinalInput name="subject" required />
        )}
      </Form.Field>
      <Form.Field required>
        <Translate as="label">Email body</Translate>
        {preview ? (
          <TextEditor value={preview.body} disabled />
        ) : (
          <FinalField name="body" validate={validators.required}>
            {({input, meta}) => (
              <>
                {meta.touched && (meta.error || meta.submitError) && (
                  <Label basic color="red" pointing="below">
                    {meta.error || meta.submitError}
                  </Label>
                )}
                <TextEditor
                  {...input}
                  value={preview ? preview.body : input.value}
                  onChange={(_, editor) =>
                    !disableChange.current && input.onChange(editor.getData())
                  }
                  disabled={!!preview}
                  required
                />
              </>
            )}
          </FinalField>
        )}
      </Form.Field>
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
      <Translate
        as={Button}
        type="submit"
        disabled={submitting || submitSucceeded || hasValidationErrors}
        primary
      >
        Send
      </Translate>
      <FormSpy subscription={{values: true}}>
        {({values}) => (
          <Button
            type="button"
            active={!!preview}
            onClick={() => togglePreview(values)}
            disabled={submitting || submitSucceeded || hasValidationErrors}
          >
            {!preview ? <Translate>Preview</Translate> : <Translate>Edit</Translate>}
          </Button>
        )}
      </FormSpy>
    </Form>
  );

  return (
    <FinalForm
      initialValues={{
        fromAddress: senders[0] && senders[0][0],
        subject: defaultSubject,
        body: defaultBody,
      }}
      onSubmit={onSubmit}
      render={renderForm}
    />
  );
}

EmailForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  personIds: PropTypes.arrayOf(PropTypes.number),
  userIds: PropTypes.arrayOf(PropTypes.number),
  roleIds: PropTypes.arrayOf(PropTypes.number),
};

EmailForm.defaultProps = {
  personIds: [],
  userIds: [],
  roleIds: [],
};
