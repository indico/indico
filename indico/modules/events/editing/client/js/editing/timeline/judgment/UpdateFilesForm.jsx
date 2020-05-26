// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import _ from 'lodash';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Form, Dropdown, Button} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {reviewEditable} from '../actions';
import * as selectors from '../selectors';
import {EditingReviewAction} from '../../../models';
import {FinalFileManager} from '../FileManager';
import {getFilesFromRevision} from '../FileManager/util';
import FinalTagInput from './TagInput';

import './JudgmentBox.module.scss';

const confirmOptions = [
  {
    value: 'confirm',
    text: Translate.string('Confirm'),
  },
  {
    value: 'confirm_and_approve',
    text: Translate.string('Confirm & Approve'),
  },
];

export default function UpdateFilesForm({setLoading}) {
  const [confirmationType, setConfirmationType] = useState('confirm');
  const lastRevision = useSelector(selectors.getLastRevision);
  const staticData = useSelector(selectors.getStaticData);
  const {eventId, contributionId, editableType} = staticData;
  const fileTypes = useSelector(selectors.getFileTypes);
  const dispatch = useDispatch();
  const files = getFilesFromRevision(fileTypes, lastRevision);
  const option = confirmOptions.find(x => x.value === confirmationType);

  const submitReview = async formData => {
    setLoading(true);
    const rv = await dispatch(
      reviewEditable(lastRevision, {
        ...formData,
        action:
          confirmationType === 'confirm_and_approve'
            ? EditingReviewAction.update_accept
            : EditingReviewAction.update,
      })
    );
    if (rv.error) {
      setLoading(false);
      return rv.error;
    }
  };

  return (
    <FinalForm
      initialValues={{comment: '', tags: lastRevision.tags.map(t => t.id), files}}
      initialValuesEqual={_.isEqual}
      subscription={{}}
      onSubmit={submitReview}
    >
      {({handleSubmit}) => (
        <>
          <Form id="judgment-form" onSubmit={handleSubmit}>
            <FinalFileManager
              name="files"
              fileTypes={fileTypes}
              files={lastRevision.files}
              uploadURL={uploadURL({
                confId: eventId,
                contrib_id: contributionId,
                type: editableType,
              })}
              mustChange
            />
            <FinalTextArea
              name="comment"
              placeholder={Translate.string('Leave a comment...')}
              required
              hideValidationError
              autoFocus
            />
            <FinalTagInput name="tags" options={staticData.tags} />
          </Form>
          <div styleName="judgment-submit-button">
            <Button.Group color="blue">
              <FinalSubmitButton form="judgment-form" label={option.text}>
                {disabled => (
                  <Dropdown
                    className="icon"
                    button
                    floating
                    disabled={disabled}
                    options={confirmOptions}
                    onChange={(e, data) => setConfirmationType(data.value)}
                    // eslint-disable-next-line react/jsx-no-useless-fragment
                    trigger={<React.Fragment />}
                  />
                )}
              </FinalSubmitButton>
            </Button.Group>
          </div>
        </>
      )}
    </FinalForm>
  );
}

UpdateFilesForm.propTypes = {
  setLoading: PropTypes.func.isRequired,
};
