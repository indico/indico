// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableURL from 'indico-url:event_editing.editable';
import React, {useCallback, useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Modal} from 'semantic-ui-react';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {Translate} from 'indico/react/i18n';
import FileManager from './FileManager';
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
  const [submissionFiles, setSubmissionFiles] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const submitRevision = async () => {
    setSubmitting(true);
    try {
      await indicoAxios.put(submitRevisionURL, {
        files: submissionFiles,
      });
    } catch (e) {
      handleAxiosError(e);
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    location.href = editableURL({confId: eventId, contrib_id: contributionId, type});
  };

  const handleChange = useCallback(files => setSubmissionFiles(files), []);
  return (
    <>
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
          <FileManager onChange={handleChange} fileTypes={fileTypes} uploadURL={uploadURL} />
        </Modal.Content>
        <Modal.Actions>
          <Button onClick={() => setOpen(false)}>
            <Translate>Cancel</Translate>
          </Button>
          <Button
            primary
            disabled={submitting || !Object.keys(submissionFiles).length}
            onClick={submitRevision}
          >
            <Translate>Save</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
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
