// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {RevisionType} from '../../models';

import {blockPropTypes} from './util';

import './ReviewComment.module.scss';

export default function ReviewComment({block, canEdit}) {
  const [editFormOpen, setEditFormOpen] = useState(false);

  const handleSubmit = async formData => {
    console.log(formData, block);
    // TODO
    setEditFormOpen(false);
  };

  return (
    <div styleName="revision-comment">
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
                  required={block.type.name !== RevisionType.acceptance}
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
        {canEdit && (
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
