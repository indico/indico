// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';
import createFileTypeURL from 'indico-url:event_editing.api_add_file_type';
import editFileTypeURL from 'indico-url:event_editing.api_edit_file_type';

import React, {useReducer} from 'react';
import PropTypes from 'prop-types';
import {Button, Icon, Loader, Message, Segment} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';
import FileTypeModal from './FileTypeModal';
import RequestConfirm from './RequestConfirm';

import './FileTypeManager.module.scss';

const initialState = {
  fileType: null,
  operation: null,
};

function fileTypesReducer(state, action) {
  switch (action.type) {
    case 'ADD_FILE_TYPE':
      return {operation: 'add', fileType: null};
    case 'EDIT_FILE_TYPE':
      return {operation: 'edit', fileType: action.fileType};
    case 'DELETE_FILE_TYPE':
      return {operation: 'delete', fileType: action.fileType};
    case 'CLEAR':
      return {...initialState};
    default:
      return state;
  }
}

export default function FileTypeManager({eventId}) {
  const [state, dispatch] = useReducer(fileTypesReducer, initialState);

  const {data, loading: isLoadingFileTypes, reFetch, lastData} = useIndicoAxios({
    url: fileTypesURL({confId: eventId}),
    camelize: true,
    trigger: eventId,
  });

  const createFileType = async formData => {
    try {
      await indicoAxios.post(createFileTypeURL({confId: eventId}), snakifyKeys(formData));
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const editFileType = async (fileTypeId, fileTypeData) => {
    const url = editFileTypeURL({confId: eventId, file_type_id: fileTypeId});

    try {
      await indicoAxios.patch(url, snakifyKeys(fileTypeData));
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const deleteFileType = async fileTypeId => {
    const url = editFileTypeURL({confId: eventId, file_type_id: fileTypeId});

    try {
      await indicoAxios.delete(url);
      reFetch();
    } catch (e) {
      handleAxiosError(e);
      return true;
    }
  };

  const fileTypes = data || lastData;
  if (isLoadingFileTypes && !lastData) {
    return <Loader inline="centered" active />;
  } else if (!fileTypes) {
    return null;
  }

  const {operation, fileType: currentFileType} = state;
  return (
    <div styleName="file-types-container">
      {fileTypes.length === 0 && (
        <Message info>
          <Translate>There are no file types defined for this event</Translate>
        </Message>
      )}
      {fileTypes.map(fileType => (
        <Segment key={fileType.id} styleName="filetype-segment">
          <div styleName="filetype">
            <div>
              <h3>{fileType.name}</h3>
              <ul styleName="file-extensions">
                {fileType.extensions.length !== 0
                  ? fileType.extensions.map(ext => <li key={ext}>{ext}</li>)
                  : Translate.string('(no extension restrictions)')}
              </ul>
            </div>
            <div styleName="actions">
              <Icon
                color="blue"
                name="pencil"
                onClick={() => dispatch({type: 'EDIT_FILE_TYPE', fileType})}
              />
              <Icon
                color="red"
                name="trash"
                onClick={() => dispatch({type: 'DELETE_FILE_TYPE', fileType})}
              />
            </div>
          </div>
        </Segment>
      ))}
      <Button primary floated="right" onClick={() => dispatch({type: 'ADD_FILE_TYPE'})}>
        <Icon name="plus" />
        <Translate>Add a new file type</Translate>
      </Button>
      {['add', 'edit'].includes(operation) && (
        <FileTypeModal
          header={
            operation === 'edit'
              ? Translate.string('Edit file type')
              : Translate.string('Create a new file type')
          }
          onSubmit={async (formData, form) => {
            if (operation === 'edit') {
              return await editFileType(currentFileType.id, getChangedValues(formData, form));
            } else {
              return await createFileType(formData);
            }
          }}
          initialValues={currentFileType ? currentFileType : undefined}
          onClose={() => dispatch({type: 'CLEAR'})}
        />
      )}
      {operation === 'delete' && (
        <RequestConfirm
          header={Translate.string('Delete file type')}
          confirmText={Translate.string('Yes')}
          cancelText={Translate.string('No')}
          onClose={() => dispatch({type: 'CLEAR'})}
          content={
            <div className="content">
              <Translate>
                Are you sure you want to delete the file type{' '}
                <Param name="fileType" value={currentFileType.name} wrapper={<strong />} />?
              </Translate>
            </div>
          }
          requestFunc={() => deleteFileType(currentFileType.id)}
          open
        />
      )}
    </div>
  );
}

FileTypeManager.propTypes = {
  eventId: PropTypes.number.isRequired,
};
