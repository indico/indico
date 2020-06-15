// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableURL from 'indico-url:event_editing.editable';
import submitRevisionURL from 'indico-url:event_editing.api_create_editable';
import apiUploadURL from 'indico-url:event_editing.api_upload';
import apiUploadExistingURL from 'indico-url:event_editing.api_upload_last_revision';

import _ from 'lodash';
import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Dropdown, Form, Modal} from 'semantic-ui-react';
import {Form as FinalForm} from 'react-final-form';

import {indicoAxios} from 'indico/utils/axios';
import {FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Param, Translate} from 'indico/react/i18n';

import {fileTypePropTypes, uploadablePropTypes} from './timeline/FileManager/util';
import {FinalFileManager} from './timeline/FileManager';

import {getFileTypes} from './timeline/selectors';
import {EditableTypeTitles, EditableType} from '../models';

export default function EditableSubmissionButton({
  eventId,
  contributionId,
  contributionCode,
  fileTypes,
  existingFiles,
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
            <Modal.Header>
              {currentType === EditableType.paper && <Translate>Submit your paper</Translate>}
              {currentType === EditableType.slides && <Translate>Submit your slides</Translate>}
              {currentType === EditableType.poster && <Translate>Submit your poster</Translate>}
            </Modal.Header>
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
                    existingFiles={existingFiles}
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
          <Translate>
            Submit <Param name="editableType" value={editableTypes[0]} />
          </Translate>
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
  fileTypes: PropTypes.objectOf(PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes))).isRequired,
  eventId: PropTypes.string.isRequired,
  contributionId: PropTypes.string.isRequired,
  contributionCode: PropTypes.string.isRequired,
  existingFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

EditableSubmissionButton.defaultProps = {
  existingFiles: [],
};
