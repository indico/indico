// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:papers.api_file_types';
import apiUploadURL from 'indico-url:papers.api_upload';
import submitRevisionURL from 'indico-url:papers.submit_revision_new';
import submitRevisionSingleURL from 'indico-url:papers.submit_revision_new_single';

import _ from 'lodash';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useDispatch} from 'react-redux';
import {AnyAction} from 'redux';
import {Form} from 'semantic-ui-react';

import {FinalFileManager} from 'indico/modules/events/editing/editing/timeline/FileManager';
import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import {fetchPaperDetails} from '../actions';

import './RevisionSubmissionForm.module.scss';

interface RevisionSubmissionFormProps {
  eventId: number;
  contributionId: number;
  children?: React.ReactNode;
}

export default function RevisionSubmissionForm({
  eventId,
  contributionId,
  children,
}: RevisionSubmissionFormProps) {
  const dispatch = useDispatch();
  const {data} = useIndicoAxios(fileTypesURL({event_id: eventId}));
  const _fileTypes = camelizeKeys(data || []);

  const submitRevision = async ({files}) => {
    let urlFunc, payload;

    if (_fileTypes.length) {
      urlFunc = submitRevisionURL;
      payload = {files};
    } else {
      urlFunc = submitRevisionSingleURL;
      payload = {files: files['-1']};
    }

    try {
      await indicoAxios.post(urlFunc({event_id: eventId, contrib_id: contributionId}), payload);
      _.defer(() => {
        dispatch(fetchPaperDetails(eventId, contributionId) as unknown as AnyAction);
      });
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  // TODO this could probably be moved into the FileManager to support (via a new prop or passing explicit
  // `null` fileTypes) the case where no file types should be displayed. in this case the `name` can be
  // something dummy/empty as it should not be displayed to users
  const fileTypes = _fileTypes.length
    ? _fileTypes
    : [
        {
          name: '', // Needs to be added empty as it is required
          extensions: [],
          allowMultipleFiles: true,
          filenameTemplate: null,
          id: -1,
        },
      ];

  if (!data) {
    return null;
  }

  return (
    <FinalForm
      onSubmit={submitRevision}
      initialValuesEqual={_.isEqual}
      initialValues={{files: {}}}
      header={<Translate>Submit paper</Translate>}
      size="large"
    >
      {fprops => (
        <Form
          id="paper-submission-form"
          onSubmit={fprops.handleSubmit}
          styleName={fileTypes.length === 1 ? 'single-file-type-form' : ''}
        >
          <FinalFileManager
            name="files"
            fileTypes={fileTypes}
            files={[]}
            uploadURL={apiUploadURL({
              event_id: eventId,
              contrib_id: contributionId,
            })}
            mustChange
          />
          {children}
        </Form>
      )}
    </FinalForm>
  );
}
