// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import submitRevisionURL from 'indico-url:papers.api_submit_revision';

import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {FileSubmission} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import UserAvatar from './UserAvatar';
import {fetchPaperInfo} from '../actions';
import {getCurrentUser, getPaperDetails} from '../selectors';

export default function SubmitRevision() {
  const {
    state: {name: stateName},
    event: {id: eventId},
    contribution: {id: contributionId},
  } = useSelector(getPaperDetails);
  const [files, setFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const currentUser = useSelector(getCurrentUser);
  const dispatch = useDispatch();

  if (stateName !== 'to_be_corrected') {
    return null;
  }

  const submitFiles = async () => {
    setSubmitting(true);

    const headers = {'content-type': 'multipart/form-data'};
    const formData = new FormData();

    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      await indicoAxios.post(
        submitRevisionURL({confId: eventId, contrib_id: contributionId}),
        formData,
        {headers}
      );
    } catch (e) {
      handleAxiosError(e, false, true);
      return;
    } finally {
      setSubmitting(false);
    }

    setFiles([]);
    dispatch(fetchPaperInfo(eventId, contributionId));
  };

  return (
    <div className="i-timeline-item" id="proposal-revision-submission-box">
      <UserAvatar user={currentUser} />
      <div className="i-timeline-item-box header-indicator-left">
        <div className="i-box-header flexrow">
          <Translate>Upload corrected revision</Translate>
        </div>
        <div className="i-box-content">
          <FileSubmission onChange={newFiles => setFiles(newFiles)} />
          <Button
            onClick={submitFiles}
            content={Translate.string('Submit new revision')}
            style={{marginTop: 10}}
            disabled={files.length === 0}
            loading={submitting}
            primary
          />
        </div>
      </div>
    </div>
  );
}
