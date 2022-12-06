// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Form, Button, Message} from 'semantic-ui-react';

import PlaceholderInfo from 'indico/react/components/PlaceholderInfo';
import TextEditor, {FinalTextEditor} from 'indico/react/components/TextEditor';
import {FinalCheckbox, FinalDropdown, FinalInput} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

export function EmailDialog({
  onClose,
  onSubmit,
  senders,
  sentEmailsCount,
  previewURL,
  previewContext,
  placeholders,
  recipientsField,
  initialFormValues,
}) {
  const [preview, setPreview] = useState(null);

  const togglePreview = async ({body, subject}) => {
    if (preview) {
      setPreview(undefined);
      return;
    }
    body = body.getData ? body.getData() : body;
    const {data} = await indicoAxios.post(
      previewURL,
      snakifyKeys({body, subject, ...previewContext})
    );
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
  const form = (
    <>
      {preview && renderPreview()}
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
          <FinalTextEditor name="body" required config={{images: false}} />
        </Form.Field>
        {placeholders.length > 0 && (
          <Form.Field>
            <PlaceholderInfo placeholders={placeholders} />
          </Form.Field>
        )}
        {recipientsField}
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
    <FinalModalForm
      id="send-email"
      size="standard"
      header={Translate.string('Send email')}
      initialValues={{
        fromAddress: senders[0][0],
        subject: '',
        body: '',
        copyForSender: false,
        ...initialFormValues,
      }}
      onClose={onClose}
      onSubmit={onSubmit}
      submitLabel={Translate.string('Send')}
      extraActions={({submitSucceeded}) => !submitSucceeded && extraActions}
      disabledUntilChange={false}
      disabledAfterSubmit
      unloadPrompt
    >
      {({submitSucceeded}) =>
        submitSucceeded ? (
          <Message positive>
            <Translate as={Message.Header}>Your email has been sent.</Translate>
            <PluralTranslate count={sentEmailsCount} as="p">
              <Singular>
                <Param name="count" value={sentEmailsCount} /> email has been sent.
              </Singular>
              <Plural>
                <Param name="count" value={sentEmailsCount} /> emails have been sent.
              </Plural>
            </PluralTranslate>
          </Message>
        ) : (
          form
        )
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
  recipientsField: PropTypes.node.isRequired,
  initialFormValues: PropTypes.object,
};

EmailDialog.defaultProps = {
  previewContext: {},
  initialFormValues: {},
  sentEmailsCount: 0,
};
