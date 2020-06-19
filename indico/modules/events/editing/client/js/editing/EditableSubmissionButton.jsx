// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableURL from 'indico-url:event_editing.editable';
import submitRevisionURL from 'indico-url:event_editing.api_create_editable';
import apiUploadURL from 'indico-url:event_editing.api_upload';
import apiUploadExistingURL from 'indico-url:event_editing.api_add_paper_file';

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Dropdown, Form, Modal} from 'semantic-ui-react';
import {Form as FinalForm} from 'react-final-form';

import {indicoAxios} from 'indico/utils/axios';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {fileTypePropTypes, uploadablePropTypes} from './timeline/FileManager/util';
import {FinalFileManager} from './timeline/FileManager';

import {getFileTypes} from './timeline/selectors';
import {EditableTypeTitles} from '../models';

export default function EditableSubmissionButton({
  eventId,
  contributionId,
  contributionCode,
  fileTypes,
  uploadableFiles,
  text,
}) {
  const [currentType, setCurrentType] = useState(null);
  const submitRevision = async formData => {
    try {
      await indicoAxios.put(
        submitRevisionURL({confId: eventId, contrib_id: contributionId, type: currentType}),
        formData
      );
    } catch (e) {
      return handleSubmitError(e);
    }
    location.href = editableURL({confId: eventId, contrib_id: contributionId, type: currentType});
  };
  const editableTypes = Object.keys(fileTypes);
  const textByType = {
    paper: Translate.string('Submit paper'),
    poster: Translate.string('Submit poster'),
    slides: Translate.string('Submit slides'),
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
            open={currentType !== null}
            onClose={() => setCurrentType(null)}
            closeIcon
            closeOnDimmerClick={false}
            closeOnEscape={false}
          >
            <Modal.Header>{textByType[currentType]}</Modal.Header>
            <Modal.Content>
              {currentType !== null && (
                <Form id="submit-editable-form" onSubmit={handleSubmit}>
                  <FinalFileManager
                    name="files"
                    fileTypes={getFileTypes({
                      staticData: {
                        fileTypes: fileTypes[currentType],
                        contributionCode,
                      },
                    })}
                    uploadURL={apiUploadURL({
                      confId: eventId,
                      contrib_id: contributionId,
                      type: currentType,
                    })}
                    uploadExistingURL={apiUploadExistingURL({
                      confId: eventId,
                      contrib_id: contributionId,
                      type: currentType,
                    })}
                    uploadableFiles={uploadableFiles}
                    mustChange
                  />
                </Form>
              )}
            </Modal.Content>
            <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
              <FinalSubmitButton form="submit-editable-form" label={Translate.string('Submit')} />
              <Button onClick={() => setCurrentType(null)}>
                <Translate>Cancel</Translate>
              </Button>
            </Modal.Actions>
          </Modal>
        )}
      </FinalForm>
      {editableTypes.length === 1 ? (
        <Button onClick={() => setCurrentType(editableTypes[0])} primary>
          {text || textByType[editableTypes[0]]}
        </Button>
      ) : (
        <Dropdown
          className="primary"
          text={Translate.string('Submit files')}
          onChange={(__, {value}) => setCurrentType(value)}
          options={editableTypes.map(editableType => ({
            text: EditableTypeTitles[editableType],
            value: editableType,
          }))}
          selectOnNavigation={false}
          selectOnBlur={false}
          value={null}
          button
        />
      )}
    </>
  );
}

EditableSubmissionButton.propTypes = {
  text: PropTypes.string,
  fileTypes: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes))).isRequired,
  eventId: PropTypes.number.isRequired,
  contributionId: PropTypes.number.isRequired,
  contributionCode: PropTypes.string.isRequired,
  uploadableFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

EditableSubmissionButton.defaultProps = {
  text: undefined,
  uploadableFiles: [],
};
