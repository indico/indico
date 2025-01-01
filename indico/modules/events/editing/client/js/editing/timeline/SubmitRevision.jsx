// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createSubmitterRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';
import uploadURL from 'indico-url:event_editing.api_upload';

import _ from 'lodash';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector, useDispatch} from 'react-redux';
import {Form} from 'semantic-ui-react';

import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {createRevision} from './actions';
import {FinalFileManager} from './FileManager';
import {getFilesFromRevision} from './FileManager/util';
import * as selectors from './selectors';

export default function SubmitRevision() {
  const {eventId, contributionId, editableType} = useSelector(selectors.getStaticData);
  const fileTypes = useSelector(selectors.getFileTypes);
  const lastRevision = useSelector(selectors.getLastRevision);
  const lastRevisionWithFiles = useSelector(selectors.getLastRevisionWithFiles);
  const dispatch = useDispatch();
  const currentUser = {
    fullName: Indico.User.name,
    avatarURL: Indico.User.avatarURL,
  };
  const files = getFilesFromRevision(fileTypes, lastRevisionWithFiles);

  const submitRevision = async formData => {
    const rv = await dispatch(
      createRevision(
        createSubmitterRevisionURL({
          event_id: eventId,
          contrib_id: contributionId,
          type: editableType,
          revision_id: lastRevision.id,
        }),
        formData
      )
    );
    if (rv.error) {
      return rv.error;
    }
  };

  return (
    <FinalForm
      initialValues={{files}}
      initialValuesEqual={_.isEqual}
      subscription={{}}
      onSubmit={submitRevision}
    >
      {({handleSubmit}) => (
        <Form onSubmit={handleSubmit}>
          <div className="i-timeline">
            <div className="i-timeline-item">
              <UserAvatar user={currentUser} />
              <div className="i-timeline-item-box header-indicator-left">
                <div className="i-box-header flexrow">
                  <Translate>Upload corrected revision</Translate>
                </div>
                <div className="i-box-content">
                  <FinalFileManager
                    name="files"
                    fileTypes={fileTypes}
                    files={lastRevisionWithFiles.files}
                    uploadURL={uploadURL({
                      event_id: eventId,
                      contrib_id: contributionId,
                      type: editableType,
                    })}
                    mustChange
                  />
                  <FinalSubmitButton label={Translate.string('Submit new revision')} />
                </div>
              </div>
            </div>
          </div>
        </Form>
      )}
    </FinalForm>
  );
}
