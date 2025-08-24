// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createFileTypeURL from 'indico-url:event_editing.api_add_file_type';
import editFileTypeURL from 'indico-url:event_editing.api_edit_file_type';
import fileTypesURL from 'indico-url:event_editing.api_file_types';

import PropTypes from 'prop-types';
import React, {useReducer} from 'react';
import {Button, Icon, Loader, Message, Segment, Popup, Label} from 'semantic-ui-react';

import {RequestConfirmDelete, TooltipIfTruncated} from 'indico/react/components';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import {EditableType} from '../../../models';

import FileTypeModal from './FileTypeModal';

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

function StatusIcon({active, icon, text}) {
  return (
    <Icon size="small" color={active ? 'blue' : 'grey'} name={icon} title={active ? text : ''} />
  );
}

StatusIcon.propTypes = {
  active: PropTypes.bool.isRequired,
  icon: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
};

export default function FileTypeManager({eventId, editableType}) {
  const [state, dispatch] = useReducer(fileTypesReducer, initialState);
  const {
    data,
    loading: isLoadingFileTypes,
    reFetch,
    lastData,
  } = useIndicoAxios(fileTypesURL({event_id: eventId, type: editableType}), {camelize: true});

  const createFileType = async formData => {
    try {
      await indicoAxios.post(createFileTypeURL({event_id: eventId, type: editableType}), formData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const editFileType = async (fileTypeId, fileTypeData) => {
    const url = editFileTypeURL({event_id: eventId, file_type_id: fileTypeId, type: editableType});

    try {
      await indicoAxios.patch(url, fileTypeData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const deleteFileType = async fileTypeId => {
    const url = editFileTypeURL({event_id: eventId, file_type_id: fileTypeId, type: editableType});

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

  const isLastPublishable = fileTypeId => {
    const publishable = fileTypes.filter(ft => ft.publishable);
    return publishable.length === 1 && publishable[0].id === fileTypeId;
  };

  const canDelete = fileType =>
    !fileType.isUsedInCondition && !fileType.isUsed && !isLastPublishable(fileType.id);
  const renderPopupContent = fileType => {
    if (canDelete(fileType)) {
      return null;
    }

    if (fileType.isUsed) {
      return <Translate>This type has files attached</Translate>;
    } else if (fileType.isUsedInCondition) {
      return <Translate>This type is used in a review condition</Translate>;
    } else {
      return <Translate>Cannot delete the only publishable type</Translate>;
    }
  };
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
          <Label ribbon>
            <StatusIcon
              active={fileType.required}
              icon="asterisk"
              text={Translate.string('File required')}
            />
            <StatusIcon
              active={fileType.allowMultipleFiles}
              icon="copy outline"
              text={Translate.string('Multiple files allowed')}
            />
            <StatusIcon
              active={fileType.publishable}
              icon="eye"
              text={Translate.string('File publishable')}
            />
          </Label>
          <Popup
            on="hover"
            disabled={canDelete(fileType)}
            position="right center"
            content={renderPopupContent(fileType)}
            trigger={
              <Icon
                style={canDelete(fileType) ? {cursor: 'pointer'} : {}}
                color="red"
                name="trash"
                corner="top right"
                disabled={!canDelete(fileType)}
                onClick={() =>
                  canDelete(fileType) && dispatch({type: 'DELETE_FILE_TYPE', fileType})
                }
              />
            }
          />
          <Icon
            style={{cursor: 'pointer'}}
            color="blue"
            name="pencil"
            corner="top right"
            onClick={() => dispatch({type: 'EDIT_FILE_TYPE', fileType})}
          />
          <div styleName="filetype-header">
            <h3>
              <TooltipIfTruncated>
                <span styleName="name">{fileType.name}</span>
              </TooltipIfTruncated>
            </h3>
            <ul styleName="file-extensions">
              {fileType.extensions.length !== 0
                ? fileType.extensions.map(ext => <li key={ext}>{ext}</li>)
                : Translate.string('(no extension restrictions)')}
            </ul>
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
          fileType={currentFileType ? currentFileType : undefined}
          onClose={() => dispatch({type: 'CLEAR'})}
        />
      )}
      <RequestConfirmDelete
        onClose={() => dispatch({type: 'CLEAR'})}
        requestFunc={() => deleteFileType(currentFileType.id)}
        open={operation === 'delete'}
      >
        {currentFileType && (
          <Translate>
            Are you sure you want to delete the file type{' '}
            <Param name="fileType" value={currentFileType.name} wrapper={<strong />} />?
          </Translate>
        )}
      </RequestConfirmDelete>
    </div>
  );
}

FileTypeManager.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
};
