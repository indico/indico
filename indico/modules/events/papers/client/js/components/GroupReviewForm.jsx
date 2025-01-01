// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Button, Form, Popup} from 'semantic-ui-react';

import {FinalRating} from 'indico/react/components/ReviewRating';
import {
  FinalDropdown,
  FinalInput,
  FinalRadio,
  FinalTextArea,
  FinalSubmitButton,
} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';

import {getReviewingQuestions, getPaperEvent} from '../selectors';

import './GroupReviewForm.module.scss';

const actionOptions = [
  {
    value: 'accept',
    text: Translate.string('Accept'),
  },
  {
    value: 'reject',
    text: Translate.string('Reject'),
  },
  {
    value: 'to_be_corrected',
    text: Translate.string('To be corrected'),
  },
];

function ReviewingQuestion({question: {id, isRequired, fieldType, fieldData}}) {
  const {
    cfp: {
      ratingRange: [minScore, maxScore],
    },
  } = useSelector(getPaperEvent);
  const fieldName = `question_${id}`;

  if (fieldType === 'text') {
    const Component = fieldData.multiline ? FinalTextArea : FinalInput;
    const props = {'data-max-words': fieldData.maxWords, 'maxLength': fieldData.maxLength};
    return <Component name={fieldName} required={isRequired} {...props} />;
  } else if (fieldType === 'bool') {
    return (
      <Form.Group>
        <FinalRadio
          name={fieldName}
          required={isRequired}
          label={Translate.string('Yes')}
          value="yes"
        />
        <FinalRadio
          name={fieldName}
          required={isRequired}
          label={Translate.string('No')}
          value="no"
        />
      </Form.Group>
    );
  } else if (fieldType === 'rating') {
    return (
      <FinalRating name={fieldName} required={isRequired} max={maxScore} min={minScore} allowNull />
    );
  } else {
    throw new Error(`Unsupported field type: ${fieldType}`);
  }
}

ReviewingQuestion.propTypes = {
  question: PropTypes.object.isRequired,
};

/**
 *
 * @param {Object} group - object with the info about the reviewing group
 * @param {Object} review - object with the data used to prefill the form's initial values
 * @param {Function} onSubmit - function invoked on the form submission
 * @param {Function} onCancel - function invoked once the user decides to stop filling in the form
 */
export default function GroupReviewForm({group, review, onSubmit, onCancel}) {
  const questions = useSelector(getReviewingQuestions)[group.name];
  const renderQuestions = () => {
    return questions.map((question, index) => {
      return (
        <Popup
          key={question.id}
          position="left center"
          content={question.description}
          disabled={!question.description}
          trigger={
            <div className="flexrow question-row">
              <div>
                <span className="question-index">{index + 1}</span>
              </div>
              <div className="question-text f-self-stretch">
                {question.title}
                {question.isRequired && (
                  <Popup
                    trigger={<i className="question-required"> *</i>}
                    content={Translate.string('Rating this question is mandatory')}
                    position="bottom center"
                  />
                )}
              </div>
              <div styleName="question-field">
                <ReviewingQuestion question={question} />
              </div>
            </div>
          }
        />
      );
    });
  };

  const initialValues = {};
  if (review) {
    initialValues.proposed_action = review.proposedAction.name;
    initialValues.comment = review.comment;

    for (const {value, question} of review.ratings) {
      if (question.fieldType === 'bool') {
        initialValues[`question_${question.id}`] = value ? 'yes' : 'no';
      } else {
        initialValues[`question_${question.id}`] = value;
      }
    }
  }

  return (
    <FinalForm onSubmit={onSubmit} subscription={{submitting: true}} initialValues={initialValues}>
      {fprops => (
        <Form onSubmit={fprops.handleSubmit} styleName="group-review-form">
          {!review && (
            <>
              <div className="form-preface">
                <Translate>
                  Reviewing in{' '}
                  <Param
                    name="group"
                    value={group.title}
                    wrapper={<div className="review-group truncate-text" />}
                  />
                </Translate>
              </div>
              {questions.length !== 0 && (
                <div className="titled-rule">
                  <Translate>Ratings</Translate>
                </div>
              )}
            </>
          )}
          {questions.length !== 0 && <div className="review-questions">{renderQuestions()}</div>}
          <div className="titled-rule">
            <Translate>Proposal</Translate>
          </div>
          <FinalDropdown
            name="proposed_action"
            options={actionOptions}
            placeholder={Translate.string('Propose an action')}
            selection
            required
          />
          <FinalTextArea
            name="comment"
            placeholder={Translate.string(
              'You may leave a comment (only visible to reviewers and judges)...'
            )}
            nullIfEmpty
          />
          <Form.Group>
            <FinalSubmitButton
              label={review ? Translate.string('Change review') : Translate.string('Submit review')}
              disabledUntilChange
            />
            <Button onClick={onCancel} disabled={fprops.submitting}>
              <Translate>Cancel</Translate>
            </Button>
          </Form.Group>
        </Form>
      )}
    </FinalForm>
  );
}

GroupReviewForm.propTypes = {
  group: PropTypes.shape({
    name: PropTypes.oneOf(['content', 'layout']).isRequired,
    title: PropTypes.string.isRequired,
    value: PropTypes.number.isRequired,
  }).isRequired,
  review: PropTypes.object,
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func,
};

GroupReviewForm.defaultProps = {
  review: null,
  onCancel: null,
};
