// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
import {DirtyInitialValue} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import {getDetails} from './selectors';

import './CommentForm.module.scss';

export default function CommentForm({
  onSubmit,
  onToggleExpand,
  initialValues,
  expanded,
  commentValue,
  onCommentChange,
  syncComment,
  setSyncComment,
}) {
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
      onCommentChange('');
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
              onChange={onCommentChange}
              name="text"
              placeholder={Translate.string('Leave a comment...')}
              hideValidationError
              required
            />
            {syncComment && (
              <DirtyInitialValue
                field="text"
                value={commentValue}
                onUpdate={() => setSyncComment(false)}
              />
            )}
            {commentFormVisible && (
              <>
                {canCreateInternalComments && (
                  <FinalCheckbox
                    label={Translate.string(
                      'Restrict visibility of this comment to other editors only'
                    )}
                    name="internal"
                    showAsToggle
                  />
                )}
                <Form.Group styleName="submit-buttons" inline>
                  <FinalSubmitButton
                    label={Translate.string('Comment', 'Leave a comment (verb)')}
                  />
                  <Button
                    disabled={fprops.submitting}
                    content={Translate.string('Cancel')}
                    onClick={() => {
                      setCommentFormVisible(false);
                      onToggleExpand(false);
                      onCommentChange('');
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
  onToggleExpand: PropTypes.func,
  initialValues: PropTypes.shape({
    text: PropTypes.string,
    internal: PropTypes.bool,
  }),
  expanded: PropTypes.bool,
  onCommentChange: PropTypes.func,
  commentValue: PropTypes.string,
  syncComment: PropTypes.bool,
  setSyncComment: PropTypes.func,
};

CommentForm.defaultProps = {
  initialValues: {
    text: '',
    internal: false,
  },
  expanded: false,
  onToggleExpand: () => {},
  onCommentChange: () => {},
  commentValue: '',
  syncComment: false,
  setSyncComment: () => {},
};
