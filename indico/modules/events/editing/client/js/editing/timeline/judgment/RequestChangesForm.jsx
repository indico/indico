// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useDispatch, useSelector} from 'react-redux';
import {Checkbox, Form} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {EditingReviewAction} from '../../../models';
import {reviewEditable} from '../actions';
import {FinalFileManager} from '../FileManager';
import {
  getFileTypes,
  getLastRevision,
  getLastRevisionWithFiles,
  getNonSystemTags,
  getStaticData,
} from '../selectors';

import FinalTagInput from './TagInput';

export default function RequestChangesForm({setLoading, onSuccess}) {
  const dispatch = useDispatch();
  const lastRevision = useSelector(getLastRevision);
  const lastRevisionWithFiles = useSelector(getLastRevisionWithFiles);
  const staticData = useSelector(getStaticData);
  const {eventId, contributionId, editableType} = staticData;
  const fileTypes = useSelector(getFileTypes);
  const tagOptions = useSelector(getNonSystemTags);
  const [uploadChanges, setUploadChanges] = useState(false);

  const requestChanges = async formData => {
    setLoading(true);
    const rv = await dispatch(
      reviewEditable(lastRevision, {
        ...formData,
        action: EditingReviewAction.requestUpdate,
      })
    );

    setLoading(false);
    if (rv.error) {
      return rv.error;
    }

    onSuccess();
  };

  return (
    <FinalForm
      onSubmit={requestChanges}
      subscription={{}}
      initialValues={{
        comment: '',
        tags: lastRevision.tags
          .filter(t => !t.system)
          .map(t => t.id)
          .sort(),
      }}
      initialValuesEqual={_.isEqual}
    >
      {fprops => (
        <Form onSubmit={fprops.handleSubmit}>
          <FinalTextArea
            name="comment"
            placeholder={Translate.string('Leave a comment...')}
            required
            hideValidationError
            autoFocus
          />
          <Form.Field>
            <Checkbox
              toggle
              label={Translate.string('Upload files')}
              checked={uploadChanges}
              onChange={(__, {checked}) => setUploadChanges(checked)}
            />
          </Form.Field>
          {uploadChanges && (
            <FinalFileManager
              name="files"
              fileTypes={fileTypes}
              files={lastRevisionWithFiles.files}
              uploadURL={uploadURL({
                event_id: eventId,
                contrib_id: contributionId,
                type: editableType,
              })}
            />
          )}
          <FinalTagInput name="tags" options={tagOptions} />
          <div style={{display: 'flex', justifyContent: 'flex-end'}}>
            <FinalSubmitButton label={Translate.string('Submit')} />
          </div>
        </Form>
      )}
    </FinalForm>
  );
}

RequestChangesForm.propTypes = {
  setLoading: PropTypes.func.isRequired,
  onSuccess: PropTypes.func.isRequired,
};
