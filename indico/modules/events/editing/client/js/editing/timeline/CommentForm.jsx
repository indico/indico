// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Button, Form} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getDetails} from './selectors';

import './CommentForm.module.scss';

export default function CommentForm({onSubmit, onToggleExpand, initialValues, expanded}) {
  const {canCreateInternalComments} = useSelector(getDetails);
  const [commentFormVisible, setCommentFormVisible] = useState(expanded);

  const InputComponent = commentFormVisible ? FinalTextArea : FinalInput;
  const inputProps = commentFormVisible ? {autoFocus: true} : {};
  const onCommentClickHandler = () => {
    if (!commentFormVisible) {
      setCommentFormVisible(true);
      onToggleExpand(true);
    }
  };
  const handleSubmit = async (formData, form) => {
    const rv = await onSubmit(formData, form);
    if (!rv) {
      setCommentFormVisible(false);
      onToggleExpand(false);
    }
  };

  return (
    <div className="f-self-stretch">
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={initialValues}
        subscription={{submitting: true}}
      >
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <InputComponent
              {...inputProps}
              onFocus={onCommentClickHandler}
              name="text"
              placeholder={Translate.string('Leave a comment...')}
              hideValidationError
              required
            />
            {commentFormVisible && (
              <>
                {canCreateInternalComments && (
                  <FinalCheckbox
                    label={Translate.string('Restrict visibility of this comment to other editors')}
                    name="internal"
                    toggle
                  />
                )}
                <Form.Group styleName="submit-buttons" inline>
                  <FinalSubmitButton label={Translate.string('Comment')} />
                  <Button
                    disabled={fprops.submitting}
                    content={Translate.string('Cancel')}
                    onClick={() => {
                      setCommentFormVisible(false);
                      onToggleExpand(false);
                      fprops.form.reset();
                    }}
                  />
                </Form.Group>
              </>
            )}
          </Form>
        )}
      </FinalForm>
    </div>
  );
}

CommentForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onToggleExpand: PropTypes.func.isRequired,
  initialValues: PropTypes.shape({
    text: PropTypes.string,
    internal: PropTypes.bool,
  }),
  expanded: PropTypes.bool,
};

CommentForm.defaultProps = {
  initialValues: {
    text: '',
    internal: false,
  },
  expanded: false,
};
