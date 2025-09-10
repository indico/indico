// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Form} from 'semantic-ui-react';

import {FinalCheckbox, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {DirtyInitialValue} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import {setDraftComment} from './actions';
import {getDetails, getDraftComment} from './selectors';

import './CommentForm.module.scss';

export default function CommentForm({
  onSubmit,
  onToggleExpand,
  initialValues,
  expanded,
  syncComment,
  setSyncComment,
  disabled,
}) {
  const dispatch = useDispatch();
  const {canCreateInternalComments} = useSelector(getDetails);
  const [commentFormVisible, setCommentFormVisible] = useState(expanded);
  const draftComment = useSelector(getDraftComment);

  const InputComponent = commentFormVisible ? FinalTextArea : FinalInput;
  const inputProps = commentFormVisible ? {autoFocus: true} : {};
  const onCommentClickHandler = () => {
    if (!commentFormVisible) {
      setCommentFormVisible(true);
      onToggleExpand(true);
    }
  };
  const onCommentChange = value => {
    dispatch(setDraftComment(value));
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
                value={draftComment}
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
                    disabled={disabled}
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
  syncComment: PropTypes.bool,
  setSyncComment: PropTypes.func,
  disabled: PropTypes.bool,
};

CommentForm.defaultProps = {
  initialValues: {
    text: '',
    internal: false,
  },
  expanded: false,
  onToggleExpand: () => {},
  syncComment: false,
  setSyncComment: () => {},
};
