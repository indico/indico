// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:papers.api_file_types';
import apiUploadURL from 'indico-url:papers.api_upload';
import paperTimelineURL from 'indico-url:papers.paper_timeline';
import submitRevisionURL from 'indico-url:papers.submit_revision';
import submitRevisionSingleURL from 'indico-url:papers.submit_revision_single';

import _ from 'lodash';
import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalFileManager} from 'indico/modules/events/editing/editing/timeline/FileManager';
import {handleSubmitError} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

interface PaperSubmissionButtonProps {
  eventId: number;
  contributionId: number;
}

export default function PaperSubmissionButton({
  eventId,
  contributionId,
}: PaperSubmissionButtonProps) {
  const [modalOpen, setModalOpen] = useState<boolean>(false);
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
    } catch (e) {
      return handleSubmitError(e);
    }
    location.href = paperTimelineURL({event_id: eventId, contrib_id: contributionId});
  };

  // TODO this could probably be moved into the FileManager to support (via a new prop or passing explicit
  // `null` fileTypes) the case where no file types should be displayed. in this case the `name` can be
  // something dummy/empty as it should not be displayed to users
  const fileTypes = _fileTypes.length
    ? _fileTypes
    : [
        {
          name: Translate.string('Paper files'),
          extensions: [],
          allowMultipleFiles: true,
          filenameTemplate: null,
          id: -1,
        },
      ];

  return (
    <>
      {data && modalOpen ? (
        <FinalModalForm
          id="paper-submission-form"
          onSubmit={submitRevision}
          initialValuesEqual={_.isEqual}
          initialValues={{files: {}}}
          header={<Translate>Submit paper</Translate>}
          onClose={() => setModalOpen(false)}
          size="large"
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
        </FinalModalForm>
      ) : null}
      <Button onClick={() => setModalOpen(true)} primary>
        <Translate>Submit paper</Translate>
      </Button>
    </>
  );
}
