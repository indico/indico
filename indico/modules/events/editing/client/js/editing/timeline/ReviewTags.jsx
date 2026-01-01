// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Form, Label, Popup} from 'semantic-ui-react';

import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {modifyReview} from './actions';
import FinalTagInput from './judgment/TagInput';
import {isTimelineOutdated} from './selectors';
import {blockPropTypes} from './util';

import './ReviewTags.module.scss';

export default function ReviewTags({block, canEdit, tagOptions}) {
  const [editFormOpen, setEditFormOpen] = useState(false);
  const isOutdated = useSelector(isTimelineOutdated);
  const dispatch = useDispatch();

  const handleSubmit = async formData => {
    const rv = await dispatch(modifyReview(block, formData));
    if (rv.error) {
      return rv.error;
    }
    setEditFormOpen(false);
  };

  return (
    <div styleName="review-tags">
      {!block.tags.length && !editFormOpen && canEdit && (
        <span styleName="no-tags">
          <Translate>No tags</Translate>
        </span>
      )}
      {editFormOpen ? (
        <div className="f-self-stretch">
          <FinalForm
            onSubmit={handleSubmit}
            initialValues={{tags: block.tags.map(t => t.id)}}
            subscription={{submitting: true}}
          >
            {fprops => (
              <Form onSubmit={fprops.handleSubmit}>
                <FinalTagInput name="tags" options={tagOptions} autoFocus />
                <Form.Group styleName="submit-buttons" inline>
                  <FinalSubmitButton label={Translate.string('Save tags')} />
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
        <div styleName="tag-list">
          {block.tags.map(tag => (
            <Label color={tag.color} key={tag.id}>
              {tag.verboseTitle}
            </Label>
          ))}
        </div>
      )}
      <div styleName="action-buttons">
        {canEdit && !isOutdated && (
          <Popup
            content={Translate.string('Edit tags')}
            position="bottom center"
            trigger={
              <a onClick={() => setEditFormOpen(!editFormOpen)} className="i-link icon-edit" />
            }
          />
        )}
      </div>
    </div>
  );
}

ReviewTags.propTypes = {
  block: PropTypes.shape(blockPropTypes).isRequired,
  canEdit: PropTypes.bool.isRequired,
  tagOptions: PropTypes.array.isRequired,
};
