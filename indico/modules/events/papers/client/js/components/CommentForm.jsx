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

import {FinalDropdown, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {canJudgePaper, canReviewPaper} from '../selectors';

/**
 * @param {Function} onSubmit - function invoked on the form submission
 * @param {Function} onToggleExpand - function called every time the text input gets/loses focus
 * @param {Object} comment - object with the data used to prefill the form's initial values
 * @param {Boolean} expanded - whether the form should be expanded on the initial render
 */
export default function CommentForm({onSubmit, onToggleExpand, comment, expanded}) {
  const [commentFormVisible, setCommentFormVisible] = useState(expanded);
  const canReview = useSelector(canReviewPaper);
  const canJudge = useSelector(canJudgePaper);
  const InputComponent = commentFormVisible ? FinalTextArea : FinalInput;
  const inputProps = commentFormVisible
    ? {autoFocus: true}
    : {
        onFocus: () => {
          setCommentFormVisible(true);
          onToggleExpand(true);
        },
      };

  const handleSubmit = async (formData, form) => {
    const error = await onSubmit(formData, form);
    if (error) {
      return error;
    }

    setCommentFormVisible(false);
    if (onToggleExpand) {
      onToggleExpand(false);
    }

    setTimeout(() => form.reset(), 0);
  };

  const visibilityOptions = {
    judges: {
      value: 'judges',
      text: Translate.string('Visible only to judges'),
    },
    reviewers: {
      value: 'reviewers',
      text: Translate.string('Visible to reviewers and judges'),
    },
    contributors: {
      value: 'contributors',
      text: Translate.string('Visible to contributors, reviewers and judges'),
    },
  };

  if (!canJudge) {
    delete visibilityOptions.judges;
  }

  const initialValues = comment ? {comment: comment.text} : {};
  // users who can't review the paper don't have the required permissions to change the comment's visibility,
  // thus there is no point in setting the initial value for the "visibility" field
  if (canReview) {
    initialValues.visibility =
      comment && comment.visibility ? comment.visibility.name : Object.keys(visibilityOptions)[0];
  }

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
              name="comment"
              placeholder={Translate.string('Leave a comment...')}
              required={commentFormVisible}
            />
            {commentFormVisible && (
              <>
                {canReview && (
                  <FinalDropdown
                    name="visibility"
                    options={Object.values(visibilityOptions)}
                    selection
                    required
                  />
                )}
                <Form.Group style={{marginBottom: 0}} inline>
                  <FinalSubmitButton
                    label={
                      comment
                        ? Translate.string('Update comment')
                        : Translate.string('Comment', 'Leave a comment (verb)')
                    }
                  />
                  <Button
                    disabled={fprops.submitting}
                    content={Translate.string('Cancel')}
                    onClick={() => {
                      setCommentFormVisible(false);
                      if (onToggleExpand) {
                        onToggleExpand(false);
                      }
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
  comment: PropTypes.shape({
    text: PropTypes.string,
    visibility: PropTypes.shape({
      name: PropTypes.oneOf(['judges', 'reviewers', 'contributors']).isRequired,
    }),
  }),
  expanded: PropTypes.bool,
};

CommentForm.defaultProps = {
  onToggleExpand: null,
  comment: null,
  expanded: false,
};
