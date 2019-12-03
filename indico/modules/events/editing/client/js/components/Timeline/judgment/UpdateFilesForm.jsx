// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import React, {useMemo, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {reviewEditable} from '../../../actions';
import * as selectors from '../../../selectors';
import {EditingReviewAction} from '../../../models';
import FileManager from '../../FileManager';
import {getFiles} from '../../FileManager/selectors';
import {mapFileTypes} from '../../FileManager/util';

import './JudgmentBox.module.scss';

export default function UpdateFilesForm({setLoading}) {
  const {eventId, contributionId, editableType, fileTypes} = useSelector(selectors.getStaticData);
  const lastRevision = useSelector(selectors.getLastRevision);
  const dispatch = useDispatch();

  const mappedFileTypes = useMemo(() => mapFileTypes(fileTypes, lastRevision.files), [
    fileTypes,
    lastRevision.files,
  ]);
  const [formFiles, setFormFiles] = useState(getFiles({fileTypes: mappedFileTypes}));

  return (
    <FinalForm
      initialValues={{comment: ''}}
      subscription={{}}
      onSubmit={async formData => {
        setLoading(true);
        const ret = await dispatch(
          reviewEditable(eventId, contributionId, editableType, lastRevision, {
            ...formData,
            files: formFiles,
            action: EditingReviewAction.update,
          })
        );
        if (ret.error) {
          setLoading(false);
          return ret.error;
        }
      }}
    >
      {({handleSubmit}) => (
        <>
          <Form id="judgment-form" onSubmit={handleSubmit}>
            <FileManager
              fileTypes={fileTypes}
              files={lastRevision.files}
              uploadURL={uploadURL({
                confId: eventId,
                contrib_id: contributionId,
                type: editableType,
              })}
              onChange={setFormFiles}
            />
            <FinalTextArea
              name="comment"
              placeholder={Translate.string('Leave a comment...')}
              hideValidationError
              autoFocus
            />
            <div>TODO: Tags field</div>
          </Form>
          <div styleName="judgment-submit-button">
            <FinalSubmitButton form="judgment-form" label={Translate.string('Confirm')} />
          </div>
        </>
      )}
    </FinalForm>
  );
}

UpdateFilesForm.propTypes = {
  setLoading: PropTypes.func.isRequired,
};
