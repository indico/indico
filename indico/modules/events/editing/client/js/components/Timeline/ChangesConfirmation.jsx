// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Divider, Form, Message} from 'semantic-ui-react';
import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './ChangesConfirmation.module.scss';

export default function ChangesConfirmation() {
  const confirmChanges = formData => {
    console.log(formData);
  };

  return (
    <div>
      <Divider />
      <FinalForm onSubmit={confirmChanges}>
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <Message
              info
              size="tiny"
              icon="exclamation circle"
              header={Translate.string('Confirmation required')}
              content={
                <p>
                  <Translate>
                    Editor uploaded changes to your paper. Please download the updated files and
                    verify their changes. If you reject them, you can upload a new version
                    afterwards.
                  </Translate>
                </p>
              }
            />
            <FinalTextArea
              name="comment"
              placeholder={Translate.string('You can leave a comment if you wish')}
            />
            <Form.Group inline styleName="submit-buttons">
              <FinalSubmitButton
                label={Translate.string('Accept')}
                color="green"
                icon="check"
                onClick={() => {
                  fprops.form.change('action', 'accept');
                }}
                disabledUntilChange={false}
              />
              <FinalSubmitButton
                label={Translate.string('Reject')}
                color="red"
                icon="times"
                onClick={() => {
                  fprops.form.change('action', 'reject');
                }}
                disabledUntilChange={false}
              />
            </Form.Group>
          </Form>
        )}
      </FinalForm>
    </div>
  );
}
