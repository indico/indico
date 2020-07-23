// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import deleteFileURL from 'indico-url:files.delete_file';
import uploadBOAFileURL from 'indico-url:abstracts.upload_boa_file';
import uploadBOAURL from 'indico-url:abstracts.upload_boa';

import React, {useState, useEffect} from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';

import {Form as FinalForm, Field} from 'react-final-form';
import {Form, Modal, Button} from 'semantic-ui-react';
import {FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {FileSubmission} from 'indico/react/components';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

async function deleteFile(uuid) {
  try {
    await indicoAxios.delete(deleteFileURL({uuid}));
  } catch (e) {
    handleAxiosError(e);
  }
}

async function uploadFile(url, file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const {data} = await indicoAxios.post(url, formData, {
      headers: {'content-type': 'multipart/form-data'},
    });
    return data;
  } catch (e) {
    handleAxiosError(e);
    return null;
  }
}

// eslint-disable-next-line react/prop-types
const DummyFileUploader = ({eventId, onFileChange}) => {
  const [uploading, setUploading] = useState(false);
  const [fileUUID, setFileUUID] = useState(null);

  useEffect(() => {
    return () => {
      if (fileUUID) {
        // XXX this will currently attempt to delete the file even
        // after having properly uploaded and saved it. not sure how
        // to solve that yet... to be seen later when implementing the
        // file manager thing properly
        deleteFile(fileUUID);
      }
    };
  }, [fileUUID]);

  const handleFileChange = async files => {
    if (!files.length) {
      setFileUUID(null);
      onFileChange(null);
      return;
    }
    const file = files[files.length - 1];
    setUploading(true);
    setFileUUID(null);
    const {uuid} = await uploadFile(uploadBOAFileURL({confId: eventId}), file);
    setFileUUID(uuid);
    onFileChange(uuid);
    setUploading(false);
  };

  return <FileSubmission disabled={uploading} onChange={handleFileChange} />;
};

export default function CustomBOAModal({eventId}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const deleteExistingBOA = async () => {
    try {
      await indicoAxios.delete(uploadBOAURL({confId: eventId}));
    } catch (e) {
      handleAxiosError(e);
      return true;
    }
  };

  const uploadExistingFile = async formData => {
    try {
      await indicoAxios.post(uploadBOAURL({confId: eventId}), formData);
    } catch (e) {
      handleAxiosError(e);
    }
  };

  const handleSubmit = async (formData, form) => {
    console.log('handleSubmit', formData, form);
    if (formData['uuid'] !== null) {
      uploadExistingFile({file: formData['uuid']});
    }
  };

  return (
    <>
      <span
        className="i-button icon-arrow-up"
        style={{marginRight: '0.3rem'}}
        onClick={() => setModalOpen(true)}
      >
        <Translate>Upload custom PDF</Translate>
      </span>
      <FinalForm
        onSubmit={handleSubmit}
        initialValues={{uuid: null}}
        subscription={{}}
        mutators={{
          setUUID: ([uuid], state, utils) => {
            utils.changeValue(state, 'uuid', () => uuid);
          },
        }}
      >
        {fprops => (
          <Modal open={modalOpen} onClose={() => setModalOpen(false)} size="small" closeIcon>
            <Modal.Header content={Translate.string('Custom book of abstracts')} />
            <Modal.Content>
              <Form onSubmit={fprops.handleSubmit} id="custom-boa-form">
                <div style={{marginBottom: '20px', textAlign: 'center'}}>
                  <DummyFileUploader
                    eventId={eventId}
                    onFileChange={uuid => fprops.form.mutators.setUUID(uuid)}
                  />
                </div>
                <Field name="uuid" render={() => null} />
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
              {/* TODO: Disable when no file is available */}
              <Button
                style={{marginRight: 'auto'}}
                onClick={() => setConfirmDeleteOpen(true)}
                negative
              >
                <Translate>Delete custom PDF</Translate>
              </Button>
              <Button onClick={() => setModalOpen(false)} content={Translate.string('Cancel')} />
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
          <Button onClick={() => setConfirmDeleteOpen(false)}>
            <Translate>Cancel</Translate>
          </Button>
          <Button
            negative
            onClick={() => {
              deleteExistingBOA();
              setConfirmDeleteOpen(false);
              setModalOpen(false);
            }}
          >
            <Translate>Delete</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
    </>
  );
}

CustomBOAModal.propTypes = {
  eventId: PropTypes.number.isRequired,
};

document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('#boa-custom-upload');
  if (!container) {
    return;
  }
  ReactDOM.render(<CustomBOAModal eventId={parseInt(container.dataset.eventId, 10)} />, container);
});
