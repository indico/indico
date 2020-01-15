// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';
import createSubmitterRevisionURL from 'indico-url:event_editing.api_create_submitter_revision';

import React from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {FinalSubmitButton} from 'indico/react/forms';
import UserAvatar from 'indico/modules/events/reviewing/components/UserAvatar';
import {FinalFileManager} from '../FileManager';
import * as selectors from '../../selectors';
import {createRevision} from '../../actions';
import {mapFileTypes} from '../FileManager/util';
import {getFiles} from '../FileManager/selectors';

export default function SubmitRevision() {
  const {eventId, contributionId, fileTypes, editableType} = useSelector(selectors.getStaticData);
  const lastRevision = useSelector(selectors.getLastRevision);
  const dispatch = useDispatch();
  const currentUser = {fullName: Indico.User.full_name, avatarBgColor: Indico.User.avatar_bg_color};
  const files = getFiles({fileTypes: mapFileTypes(fileTypes, lastRevision.files)});

  const submitRevision = async formData => {
    const rv = await dispatch(
      createRevision(
        createSubmitterRevisionURL({
          confId: eventId,
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
    <FinalForm initialValues={{files}} subscription={{}} onSubmit={submitRevision}>
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
                    files={lastRevision.files}
                    uploadURL={uploadURL({
                      confId: eventId,
                      contrib_id: contributionId,
                      type: editableType,
                    })}
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
