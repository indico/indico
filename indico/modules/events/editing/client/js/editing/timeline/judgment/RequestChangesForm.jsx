// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Checkbox, Form} from 'semantic-ui-react';

import {FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {FinalFileManager} from '../FileManager';
import {
  getFileTypes,
  getLastRevisionWithFiles,
  getNonSystemTags,
  getStaticData,
} from '../selectors';

import FinalTagInput from './TagInput';

export default function RequestChangesForm() {
  const lastRevisionWithFiles = useSelector(getLastRevisionWithFiles);
  const staticData = useSelector(getStaticData);
  const {eventId, contributionId, editableType} = staticData;
  const fileTypes = useSelector(getFileTypes);
  const tagOptions = useSelector(getNonSystemTags);
  const [uploadChanges, setUploadChanges] = useState(false);

  return (
    <>
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
    </>
  );
}
