// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useReducer} from 'react';
import {
  Button,
  Icon,
  Loader,
  Message,
  Segment,
  Popup,
  Label,
  SemanticICONS,
} from 'semantic-ui-react';

import {RequestConfirmDelete, TooltipIfTruncated} from 'indico/react/components';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import FileTypeModal from './FileTypeModal';

import './FileTypeManager.module.scss';

interface FileTypeManagerProps {
  eventId: number;
  getAllURLFn: (params?) => string;
  createURLFn: (params?) => string;
  editURLFn: (params?) => string;
  hideAccepted?: boolean;
  allowDeleteLastType?: boolean;
}

interface FileTypeManagerState {
  fileType: string;
  operation: 'add' | 'edit' | 'delete';
}

const initialState: FileTypeManagerState = {
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

function StatusIcon({active, icon, text}: {active: boolean; icon: SemanticICONS; text: string}) {
  return (
    <Icon size="small" color={active ? 'blue' : 'grey'} name={icon} title={active ? text : ''} />
  );
}

export default function FileTypeManager({
  eventId,
  getAllURLFn,
  createURLFn,
  editURLFn,
  hideAccepted = false,
  allowDeleteLastType = false,
}: FileTypeManagerProps) {
  const [state, dispatch] = useReducer(fileTypesReducer, initialState);
  const {
    data,
    loading: isLoadingFileTypes,
    reFetch,
    lastData,
  } = useIndicoAxios(getAllURLFn({event_id: eventId}), {camelize: true});

  const createFileType = async formData => {
    try {
      await indicoAxios.post(createURLFn({event_id: eventId}), formData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const editFileType = async (fileTypeId, fileTypeData) => {
    const url = editURLFn({event_id: eventId, file_type_id: fileTypeId});

    try {
      await indicoAxios.patch(url, fileTypeData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const deleteFileType = async fileTypeId => {
    const url = editURLFn({event_id: eventId, file_type_id: fileTypeId});

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

  const displayHideAcceptedWarning = hideAccepted && fileTypes.some(ft => ft.publishable);
  const displayNothingShownWarning =
    fileTypes?.length && !hideAccepted && !fileTypes.some(ft => ft.publishable);

  const isLastPublishable = fileTypeId => {
    const publishable = fileTypes.filter(ft => ft.publishable);
    return publishable.length === 1 && publishable[0].id === fileTypeId;
  };

  const canDelete = fileType =>
    !fileType.isUsedInCondition &&
    !fileType.isUsed &&
    (allowDeleteLastType || !isLastPublishable(fileType.id));

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
      {displayHideAcceptedWarning && (
        <Message warning>
          <Translate>
            There are publishable file types that will not be displayed due to the 'Hide Accepted'
            setting being enabled.
          </Translate>
        </Message>
      )}
      {displayNothingShownWarning && (
        <Message warning>
          <Translate>
            No file types will be shown as there are no publishable file types and the 'Hide
            Accepted' setting is disabled.
          </Translate>
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
