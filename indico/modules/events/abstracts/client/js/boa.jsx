// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadBOAFileURL from 'indico-url:abstracts.upload_boa_file';
import customBOAURL from 'indico-url:abstracts.manage_custom_boa';

import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';

import {Form as FinalForm} from 'react-final-form';
import {Form, Modal, Button} from 'semantic-ui-react';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {FinalSingleFileManager} from 'indico/react/components';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {fileDetailsShape} from 'indico/react/components/files/props';

export default function CustomBOAModal({eventId, initialFile}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const deleteExistingBOA = async () => {
    setDeleting(true);
    try {
      await indicoAxios.delete(customBOAURL({confId: eventId}));
    } catch (e) {
      handleAxiosError(e);
      setDeleting(false);
      return;
    }
    location.reload();
  };

  const handleSubmit = async ({file}) => {
    try {
      await indicoAxios.post(customBOAURL({confId: eventId}), {file});
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  return (
    <>
      <span
        className="i-button icon-arrow-up"
        style={{marginRight: '0.3rem'}}
        onClick={() => setModalOpen(true)}
      >
        {initialFile ? (
          <Translate>Manage custom PDF</Translate>
        ) : (
          <Translate>Upload custom PDF</Translate>
        )}
      </span>
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={{file: initialFile ? initialFile.uuid : null}}
        subscription={{submitting: true}}
      >
        {fprops => (
          <Modal
            open={modalOpen}
            onClose={() => setModalOpen(false)}
            size="small"
            closeIcon={!fprops.submitting}
            closeOnEscape={!fprops.submitting}
            closeOnDimmerClick={!fprops.submitting}
          >
            <Modal.Header content={Translate.string('Custom Book of Abstracts')} />
            <Modal.Content>
              <Form onSubmit={fprops.handleSubmit} id="custom-boa-form">
                <div style={{marginBottom: '20px', textAlign: 'center'}}>
                  <FinalSingleFileManager
                    name="file"
                    validExtensions={['pdf']}
                    initialFileDetails={initialFile}
                    uploadURL={uploadBOAFileURL({confId: eventId})}
                    required
                    hideValidationError
                  />
                </div>
                <div className="description" style={{margin: '10px'}}>
                  <Translate>
                    You have the possibility to upload a custom PDF for your book of abstracts.
                    Please note that when a PDF this will be the only one available for download in
                    the display view of the event. To make the customly generated file available
                    again you will have to delete the uploaded PDF.
                  </Translate>
                </div>
              </Form>
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              {initialFile !== null && (
                <Button
                  style={{marginRight: 'auto'}}
                  onClick={() => setConfirmDeleteOpen(true)}
                  disabled={fprops.submitting}
                  negative
                >
                  <Translate>Delete custom PDF</Translate>
                </Button>
              )}
              <Button onClick={() => setModalOpen(false)} disabled={fprops.submitting}>
                <Translate>Cancel</Translate>
              </Button>
              <FinalSubmitButton form="custom-boa-form" label={Translate.string('Upload BOA')} />
            </Modal.Actions>
          </Modal>
        )}
      </FinalForm>
      <Modal
        open={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        size="tiny"
        closeOnDimmerClick={false}
      >
        <Modal.Header content={Translate.string('Confirm deletion')} />
        <Modal.Content
          content={Translate.string('Do you really want to delete the uploaded custom PDF?')}
        />
        <Modal.Actions>
          <Button onClick={() => setConfirmDeleteOpen(false)} disabled={deleting}>
            <Translate>Cancel</Translate>
          </Button>
          <Button negative onClick={deleteExistingBOA} disabled={deleting} loading={deleting}>
            <Translate>Delete</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
    </>
  );
}

CustomBOAModal.propTypes = {
  eventId: PropTypes.number.isRequired,
  initialFile: fileDetailsShape,
};

CustomBOAModal.defaultProps = {
  initialFile: null,
};

document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('#boa-custom-upload');
  if (!container) {
    return;
  }
  const eventId = parseInt(container.dataset.eventId, 10);
  const customFile = JSON.parse(container.dataset.file);
  ReactDOM.render(<CustomBOAModal eventId={eventId} initialFile={customFile} />, container);
});
