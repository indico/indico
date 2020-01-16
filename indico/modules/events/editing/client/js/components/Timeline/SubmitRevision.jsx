// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';
import createSubmitterRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';

import React, {useMemo, useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {Button} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import FileManager from '../FileManager';
import * as selectors from '../../selectors';
import {createRevision} from '../../actions';
import {mapFileTypes} from '../FileManager/util';
import {getFiles} from '../FileManager/selectors';

export default function SubmitRevision() {
  const {eventId, contributionId, fileTypes, editableType} = useSelector(selectors.getStaticData);
  const lastRevision = useSelector(selectors.getLastRevision);
  const [submitting, setSubmitting] = useState(false);
  const dispatch = useDispatch();
  const currentUser = {fullName: Indico.User.full_name, avatarBgColor: Indico.User.avatar_bg_color};
  const mappedFileTypes = useMemo(() => mapFileTypes(fileTypes, lastRevision.files), [
    fileTypes,
    lastRevision.files,
  ]);
  const [submissionFiles, setSubmissionFiles] = useState(getFiles({fileTypes: mappedFileTypes}));

  const submitRevision = async () => {
    setSubmitting(true);
    const rv = await dispatch(
      createRevision(
        createSubmitterRevisionURL({
          confId: eventId,
          contrib_id: contributionId,
          type: editableType,
          revision_id: lastRevision.id,
        }),
        {files: submissionFiles}
      )
    );
    setSubmitting(false);
    if (rv.error) {
      return rv.error;
    }
  };

  return (
    <div className="i-timeline">
      <div className="i-timeline-item">
        <UserAvatar user={currentUser} />
        <div className="i-timeline-item-box header-indicator-left">
          <div className="i-box-header flexrow">
            <Translate>Upload corrected revision</Translate>
          </div>
          <div className="i-box-content">
            <FileManager
              onChange={setSubmissionFiles}
              fileTypes={fileTypes}
              files={lastRevision.files}
              uploadURL={uploadURL({
                confId: eventId,
                contrib_id: contributionId,
                type: editableType,
              })}
            />
            <Button primary disabled={submitting} onClick={submitRevision}>
              <Translate>Submit new revision</Translate>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
