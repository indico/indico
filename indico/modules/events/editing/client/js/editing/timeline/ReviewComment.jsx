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

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {RevisionTypeStates} from '../../models';

import {modifyReviewComment} from './actions';
import {isTimelineOutdated} from './selectors';
import {blockPropTypes} from './util';

import './ReviewComment.module.scss';

export default function ReviewComment({block, canEdit}) {
  const [editFormOpen, setEditFormOpen] = useState(false);
  const isOutdated = useSelector(isTimelineOutdated);
  const dispatch = useDispatch();

  const handleSubmit = async formData => {
    const rv = await dispatch(modifyReviewComment(block, formData));
    if (rv.error) {
      return rv.error;
    }
    setEditFormOpen(false);
  };

  return (
    <div styleName="review-comment">
      {editFormOpen ? (
        <div className="f-self-stretch">
          <FinalForm
            onSubmit={handleSubmit}
            initialValues={{text: block.comment}}
            subscription={{submitting: true}}
          >
            {fprops => (
              <Form onSubmit={fprops.handleSubmit}>
                <FinalTextArea
                  name="text"
                  placeholder={Translate.string('Leave a comment...')}
                  autoFocus
                  required={RevisionTypeStates[block.type.name] !== 'accepted'}
                  hideValidationError
                />
                <Form.Group styleName="submit-buttons" inline>
                  <FinalSubmitButton label={Translate.string('Save changes')} />
                  <Button
                    disabled={fprops.submitting}
                    content={Translate.string('Cancel')}
                    onClick={() => {
                      setEditFormOpen(false);
                    }}
                  />
                </Form.Group>
              </Form>
            )}
          </FinalForm>
        </div>
      ) : (
        <div className="markdown-text" dangerouslySetInnerHTML={{__html: block.commentHtml}} />
      )}
      <div styleName="action-buttons">
        {canEdit && !isOutdated && (
          <a
            onClick={() => setEditFormOpen(!editFormOpen)}
            className="i-link icon-edit"
            title={Translate.string('Edit review comment')}
          />
        )}
      </div>
    </div>
  );
}

ReviewComment.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  canEdit: PropTypes.bool.isRequired,
};
