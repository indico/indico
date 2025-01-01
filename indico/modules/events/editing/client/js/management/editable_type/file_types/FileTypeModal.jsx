// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Header, Icon, Message} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalInput, unsortedArraysEqual} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Param, Translate} from 'indico/react/i18n';

import ExtensionList from './ExtensionList';

export default function FileTypeModal({onClose, onSubmit, fileType, header}) {
  const handleSubmit = async (formData, form) => {
    const error = await onSubmit(formData, form);
    if (error) {
      return error;
    }
    onClose();
  };

  const {name, filenameTemplate, extensions, required, allowMultipleFiles, publishable} = fileType;
  return (
    <FinalModalForm
      id="file-type"
      onSubmit={handleSubmit}
      onClose={onClose}
      header={header}
      initialValues={{
        name,
        extensions,
        required,
        publishable,
        filename_template: filenameTemplate,
        allow_multiple_files: allowMultipleFiles,
      }}
    >
      {fileType.isUsed && (
        <Message visible warning>
          <Message.Content>
            <Icon name="warning" size="large" />
            <Translate>Take into account that this file type has files attached to it.</Translate>
          </Message.Content>
        </Message>
      )}
      <FinalInput name="name" label={Translate.string('Name')} required />
      <FinalInput
        name="filename_template"
        label={Translate.string('Filename template')}
        description={
          <Translate>
            Glob-style filename template that all files of this type have to conform to (e.g.{' '}
            <Param name="example" value="*_paper" wrapper={<code />} />
            ). No dots allowed. It is possible to use{' '}
            <Param name="placeholder" value="{code}" wrapper={<code />} /> as a placeholder for the
            contribution program code.
          </Translate>
        }
        pattern="^[^.]*$"
        nullIfEmpty
      />
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
        name="allow_multiple_files"
        label={Translate.string('Multiple files')}
        description={<Translate>Whether the file type allows uploading multiple files</Translate>}
      />
      <FinalCheckbox
        name="publishable"
        label={Translate.string('Publishable')}
        description={<Translate>Whether the files of this type can be published</Translate>}
      />
    </FinalModalForm>
  );
}

FileTypeModal.propTypes = {
  onClose: PropTypes.func,
  onSubmit: PropTypes.func.isRequired,
  header: PropTypes.string.isRequired,
  fileType: PropTypes.object,
};

FileTypeModal.defaultProps = {
  fileType: {
    name: null,
    extensions: [],
    required: false,
    allowMultipleFiles: false,
    publishable: false,
    isUsed: false,
    filenameTemplate: null,
  },
  onClose: null,
};
