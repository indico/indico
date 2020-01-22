// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableURL from 'indico-url:event_editing.editable';

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Form, Modal} from 'semantic-ui-react';
import {Form as FinalForm} from 'react-final-form';
import {indicoAxios} from 'indico/utils/axios';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {FinalFileManager} from './FileManager';
import {fileTypePropTypes} from './FileManager/util';

export default function EditableSubmissionButton({
  eventId,
  contributionId,
  uploadURL,
  fileTypes,
  type,
  submitRevisionURL,
}) {
  const [open, setOpen] = useState(false);

  const submitRevision = async formData => {
    try {
      await indicoAxios.put(submitRevisionURL, formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.href = editableURL({confId: eventId, contrib_id: contributionId, type});
  };

  return (
    <>
      <FinalForm
        onSubmit={submitRevision}
        subscription={{}}
        initialValuesEqual={_.isEqual}
        initialValues={{files: {}}}
      >
        {({handleSubmit}) => (
          <Modal
            open={open}
            onClose={() => setOpen(false)}
            closeIcon
            closeOnDimmerClick={false}
            closeOnEscape={false}
          >
            <Modal.Header>
              {type === 'paper' && <Translate>Submit your paper</Translate>}
              {type === 'slides' && <Translate>Submit your slides</Translate>}
            </Modal.Header>
            <Modal.Content>
              <Form id="submit-editable-form" onSubmit={handleSubmit}>
                <FinalFileManager name="files" fileTypes={fileTypes} uploadURL={uploadURL} />
              </Form>
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              <FinalSubmitButton form="submit-editable-form" label={Translate.string('Submit')} />
              <Button onClick={() => setOpen(false)}>
                <Translate>Cancel</Translate>
              </Button>
            </Modal.Actions>
          </Modal>
        )}
      </FinalForm>
      <button type="submit" className="i-button highlight" onClick={() => setOpen(true)}>
        <Translate>Submit Files</Translate>
      </button>
    </>
  );
}

EditableSubmissionButton.propTypes = {
  uploadURL: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  submitRevisionURL: PropTypes.string.isRequired,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  eventId: PropTypes.string.isRequired,
  contributionId: PropTypes.string.isRequired,
};
