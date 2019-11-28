// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {reviewEditable} from '../../../actions';
import * as selectors from '../../../selectors';
import {blockPropTypes} from '../util';

import './JudgmentBox.module.scss';

export default function AcceptRejectForm({block, action, setLoading}) {
  const {eventId, contributionId, editableType} = useSelector(selectors.getStaticData);
  const dispatch = useDispatch();

  return (
    <FinalForm
      initialValues={{comment: ''}}
      onSubmit={async formData => {
        setLoading(true);
        const ret = await dispatch(
          reviewEditable(eventId, contributionId, editableType, block, {...formData, action})
        );
        if (ret.error) {
          setLoading(false);
          return ret.error;
        }
      }}
      subscription={{}}
    >
      {({handleSubmit}) => (
        <>
          <Form id="judgment-form" onSubmit={handleSubmit}>
            <FinalTextArea
              name="comment"
              placeholder={Translate.string('Leave a comment...')}
              hideValidationError
              autoFocus
              required={action === 'reject'}
              /* otherwise changing required doesn't work properly if the field has been touched */
              key={action}
            />
            <div>TODO: Tags field</div>
          </Form>
          <div styleName="judgment-submit-button">
            <FinalSubmitButton
              form="judgment-form"
              label={Translate.string('Confirm')}
              disabledUntilChange={action === 'reject'}
            />
          </div>
        </>
      )}
    </FinalForm>
  );
}

AcceptRejectForm.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  action: PropTypes.oneOf(['accept', 'reject']).isRequired,
  setLoading: PropTypes.func.isRequired,
};
