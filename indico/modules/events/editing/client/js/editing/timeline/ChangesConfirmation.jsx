// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Field, Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Divider, Form, Message} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {confirmEditableChanges} from './actions';
import {getLastRevision} from './selectors';

import './ChangesConfirmation.module.scss';

export default function ChangesConfirmation() {
  const lastRevision = useSelector(getLastRevision);
  const dispatch = useDispatch();

  const confirmChanges = async formData => {
    const rv = await dispatch(confirmEditableChanges(lastRevision, formData));
    if (rv.error) {
      return rv.error;
    }
  };

  return (
    <div>
      <Divider />
      <FinalForm onSubmit={confirmChanges} initialValues={{comment: ''}} subscription={{}}>
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
            <Form.Group styleName="submit-buttons">
              <Field name="action" subscription={{value: true}}>
                {({input: {value: currentAction}}) => (
                  <>
                    <FinalSubmitButton
                      label={Translate.string('Accept')}
                      color="green"
                      icon="check"
                      onClick={() => {
                        fprops.form.change('action', 'accept');
                      }}
                      disabledUntilChange={false}
                      activeSubmitButton={currentAction === 'accept'}
                    />
                    <FinalSubmitButton
                      label={Translate.string('Reject')}
                      color="red"
                      icon="times"
                      onClick={() => {
                        fprops.form.change('action', 'reject');
                      }}
                      disabledUntilChange={false}
                      activeSubmitButton={currentAction === 'reject'}
                    />
                  </>
                )}
              </Field>
            </Form.Group>
          </Form>
        )}
      </FinalForm>
    </div>
  );
}
