// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Header, Modal} from 'semantic-ui-react';
import {
  FinalCheckbox,
  FinalField,
  FinalInput,
  FinalSubmitButton,
  unsortedArraysEqual,
} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import ExtensionList from './ExtensionList';

export default function FileTypeModal({onClose, onSubmit, initialValues, header}) {
  const handleSubmit = async (formData, form) => {
    const error = await onSubmit(formData, form);
    if (error) {
      return error;
    }
    onClose();
  };

  return (
    <FinalForm
      onSubmit={handleSubmit}
      subscription={{submitting: true}}
      initialValues={initialValues}
    >
      {fprops => (
        <Modal
          onClose={onClose}
          size="tiny"
          closeIcon={!fprops.submitting}
          closeOnDimmerClick={!fprops.submitting}
          open
        >
          <Modal.Header content={header} />
          <Modal.Content>
            <Form id="file-type-form" onSubmit={fprops.handleSubmit}>
              <FinalInput name="name" label={Translate.string('Name')} required />
              <FinalField
                name="extensions"
                component={ExtensionList}
                label={Translate.string('Extensions')}
                isEqual={unsortedArraysEqual}
                description={
                  <Translate>
                    Allowed file extensions. If left empty, there are no extension restrictions
                  </Translate>
                }
              />
              <Header>Options</Header>
              <FinalCheckbox
                name="required"
                label={Translate.string('File required')}
                description={<Translate>Whether the file type is mandatory</Translate>}
              />
              <FinalCheckbox
                name="allowMultipleFiles"
                label={Translate.string('Multiple files')}
                description={
                  <Translate>Whether the file type allows uploading multiple files</Translate>
                }
              />
              <FinalCheckbox
                name="publishable"
                label={Translate.string('Publishable')}
                description={<Translate>Whether the files of this type can be published</Translate>}
              />
            </Form>
          </Modal.Content>
          <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
            <FinalSubmitButton form="file-type-form" label={Translate.string('Submit')} />
            <Button onClick={onClose} disabled={fprops.submitting}>
              <Translate>Cancel</Translate>
            </Button>
          </Modal.Actions>
        </Modal>
      )}
    </FinalForm>
  );
}

FileTypeModal.propTypes = {
  onClose: PropTypes.func,
  onSubmit: PropTypes.func.isRequired,
  header: PropTypes.string.isRequired,
  initialValues: PropTypes.object,
};

FileTypeModal.defaultProps = {
  initialValues: {
    name: null,
    extensions: [],
    required: false,
    allowMultipleFiles: false,
    publishable: false,
  },
  onClose: null,
};
