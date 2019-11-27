// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Button, Dropdown, Form} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalCheckbox, FinalInput, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import JudgmentBox from './judgment/JudgmentBox';
import {blockPropTypes} from './util';

import './ReviewForm.module.scss';

const judgmentOptions = [
  {
    value: 'accept',
    text: Translate.string('Accept'),
    class: 'accepted',
  },
  {
    value: 'reject',
    text: Translate.string('Reject'),
    class: 'rejected',
  },
  {
    value: 'update',
    text: Translate.string('Make changes'),
    class: 'needs-submitter-confirmation',
  },
  {
    value: 'request_update',
    text: Translate.string('Request changes'),
    class: 'needs-submitter-changes',
  },
];

export default function ReviewForm({block}) {
  const currentUser = {
    fullName: Indico.User.full_name,
    avatarBgColor: Indico.User.avatar_bg_color,
  };

  const [commentFormVisible, setCommentFormVisible] = useState(false);
  const [judgmentType, setJudgmentType] = useState(null);
  const onCommentClickHandler = () => {
    if (!commentFormVisible) {
      setCommentFormVisible(true);
    }
  };

  const InputComponent = commentFormVisible ? FinalTextArea : FinalInput;
  const inputProps = commentFormVisible ? {autoFocus: true} : {};
  const judgmentForm = (
    <div className="flexrow">
      <div className="f-self-stretch">
        <FinalForm
          onSubmit={() => {}}
          initialValues={{comment: '', protected: false}}
          subscription={{submitting: true}}
        >
          {fprops => (
            <Form onSubmit={fprops.handleSubmit}>
              <InputComponent
                {...inputProps}
                onFocus={onCommentClickHandler}
                name="comment"
                placeholder={Translate.string('Leave a comment...')}
                hideValidationError
                required
              />
              {commentFormVisible && (
                <>
                  <FinalCheckbox
                    label={Translate.string('Restrict visibility of this comment to other editors')}
                    name="protected"
                    toggle
                  />
                  <Form.Group inline>
                    <FinalSubmitButton label={Translate.string('Comment')} />
                    <Button
                      disabled={fprops.submitting}
                      content={Translate.string('Cancel')}
                      onClick={() => {
                        setCommentFormVisible(false);
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
      {!commentFormVisible && (
        <div className="review-trigger flexrow">
          <span className="comment-or-review">
            <Translate>or</Translate>
          </span>
          <Dropdown
            className="judgment-btn"
            text={Translate.string('Judge')}
            direction="left"
            button
            floating
          >
            <Dropdown.Menu>
              {judgmentOptions.map(({value, text}) => (
                <Dropdown.Item key={value} onClick={() => setJudgmentType(value)}>
                  {text}
                </Dropdown.Item>
              ))}
            </Dropdown.Menu>
          </Dropdown>
        </div>
      )}
    </div>
  );

  return (
    <div className="i-timeline-item review-timeline-input">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box footer-only header-indicator-left">
        <div className="i-box-footer" style={{overflow: 'visible'}}>
          {judgmentType ? (
            <JudgmentBox
              block={block}
              judgmentType={judgmentType}
              onClose={() => setJudgmentType(null)}
              options={judgmentOptions}
            />
          ) : (
            judgmentForm
          )}
        </div>
      </div>
    </div>
  );
}

ReviewForm.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
};
