// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:papers.api_file_types';
import apiUploadURL from 'indico-url:papers.api_upload';
import submitRevisionURL from 'indico-url:papers.submit_revision';

import _ from 'lodash';
import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {FinalFileManager} from 'indico/modules/events/editing/editing/timeline/FileManager';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

type OnSubmitFn = (type: string, formData: unknown) => Promise<void> | void;

interface PaperSubmissionButtonProps {
  eventId: number;
  contributionId: number;
  onSubmit?: OnSubmitFn;
}

export default function PaperSubmissionButton({
  eventId,
  contributionId,
  onSubmit,
}: PaperSubmissionButtonProps) {
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const {data} = useIndicoAxios(fileTypesURL({event_id: eventId}));
  const fileTypes = camelizeKeys(data || []);

  const submitRevision = async formData => {
    try {
      if (onSubmit) {
        await onSubmit('paper', formData);
      } else {
        await indicoAxios.post(
          submitRevisionURL({event_id: eventId, contrib_id: contributionId}),
          formData
        );
      }
    } catch (e) {
      return handleSubmitError(e);
    }
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
                  name="files"
                  fileTypes={fileTypes}
                  files={[]}
                  uploadURL={apiUploadURL({
                    event_id: eventId,
                    contrib_id: contributionId,
                  })}
                  mustChange
                />
              </Form>
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              <FinalSubmitButton form="submit-papers-form" label={Translate.string('Submit')} />
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
