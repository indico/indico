// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiUploadExistingURL from 'indico-url:event_editing.api_add_contribution_file';
import submitRevisionURL from 'indico-url:event_editing.api_create_editable';
import apiUploadURL from 'indico-url:event_editing.api_upload';
import editableURL from 'indico-url:event_editing.editable';

import _ from 'lodash';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {FinalFileManager} from 'indico/modules/events/editing/editing/timeline/FileManager';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

type OnSubmitFn = (type: string, formData: unknown) => Promise<void> | void;

interface UploadableFile {
  filename: string;
  downloadURL: string;
  id: number;
}

interface PaperSubmissionButtonProps {
  eventId: number;
  contributionId: number;
  uploadableFiles?: UploadableFile[];
  onSubmit?: OnSubmitFn;
}

export default function PaperSubmissionButton({
  eventId,
  contributionId,
  uploadableFiles = [],
  onSubmit,
}: PaperSubmissionButtonProps) {
  const [modalOpen, setModalOpen] = useState<boolean>(false);

  const submitRevision = async formData => {
    try {
      if (onSubmit) {
        await onSubmit('paper', formData);
      } else {
        await indicoAxios.put(
          submitRevisionURL({event_id: eventId, contrib_id: contributionId}),
          formData
        );
      }
    } catch (e) {
      return handleSubmitError(e);
    }
    location.href = editableURL({event_id: eventId, contrib_id: contributionId});
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
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            closeIcon
            closeOnDimmerClick={false}
            closeOnEscape={false}
          >
            <Translate as={Modal.Header}>{Translate.string('Submit paper')}</Translate>
            <Modal.Content>
              <Form id="submit-papers-form" onSubmit={handleSubmit}>
                <FinalFileManager
                  uploadableFiles="paper"
                  name="files"
                  fileTypes={[]}
                  uploadURL={apiUploadURL({
                    event_id: eventId,
                    contrib_id: contributionId,
                  })}
                  uploadExistingURL={apiUploadExistingURL({
                    event_id: eventId,
                    contrib_id: contributionId,
                  })}
                  files={uploadableFiles}
                  mustChange
                />
              </Form>
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              <FinalSubmitButton form="submit-editable-form" label={Translate.string('Submit')} />
              <Button onClick={() => setModalOpen(true)}>
                <Translate>Cancel</Translate>
              </Button>
            </Modal.Actions>
          </Modal>
        )}
      </FinalForm>
      <Button onClick={() => setModalOpen(true)} primary>
        <Translate>Submit paper</Translate>
      </Button>
    </>
  );
}
