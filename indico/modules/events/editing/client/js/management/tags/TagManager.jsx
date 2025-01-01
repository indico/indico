// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createTagURL from 'indico-url:event_editing.api_create_tag';
import editTagURL from 'indico-url:event_editing.api_edit_tag';
import tagsURL from 'indico-url:event_editing.api_tags';

import PropTypes from 'prop-types';
import React, {useReducer} from 'react';
import {Button, Icon, Label, Loader, Message, Segment, Popup} from 'semantic-ui-react';

import {RequestConfirmDelete} from 'indico/react/components';
import {getChangedValues, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Param, Translate} from 'indico/react/i18n';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';

import TagModal from './TagModal';

import './TagManager.module.scss';

const initialState = {
  tag: null,
  operation: null,
};

function tagsReducer(state, action) {
  switch (action.type) {
    case 'ADD_TAG':
      return {operation: 'add', tag: null};
    case 'EDIT_TAG':
      return {operation: 'edit', tag: action.tag};
    case 'DELETE_TAG':
      return {operation: 'delete', tag: action.tag};
    case 'CLEAR':
      return {...initialState};
    default:
      return state;
  }
}

export default function TagManager({eventId}) {
  const [state, dispatch] = useReducer(tagsReducer, initialState);
  const {data, loading: isLoadingTags, reFetch, lastData} = useIndicoAxios(
    tagsURL({event_id: eventId}),
    {camelize: true}
  );

  const createTag = async formData => {
    try {
      await indicoAxios.post(createTagURL({event_id: eventId}), formData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const editTag = async (tagId, tagData) => {
    const url = editTagURL({event_id: eventId, tag_id: tagId});

    try {
      await indicoAxios.patch(url, tagData);
      reFetch();
    } catch (e) {
      return handleSubmitError(e);
    }
  };

  const deleteTag = async tagId => {
    const url = editTagURL({event_id: eventId, tag_id: tagId});

    try {
      await indicoAxios.delete(url);
      reFetch();
    } catch (e) {
      handleAxiosError(e);
      return true;
    }
  };

  const tags = data || lastData;
  if (isLoadingTags && !lastData) {
    return <Loader inline="centered" active />;
  } else if (!tags) {
    return null;
  }

  const {operation, tag: currentTag} = state;
  return (
    <div styleName="tags-container">
      {tags.map(tag => (
        <Segment key={tag.id} styleName="tag-segment">
          <Label color={tag.color}>{tag.verboseTitle}</Label>
          <div styleName="tag-actions">
            <Popup
              on="hover"
              position="right center"
              disabled={!tag.system}
              trigger={
                <span>
                  <Icon
                    name="pencil"
                    color="grey"
                    size="small"
                    title={Translate.string('Edit tag')}
                    onClick={() => dispatch({type: 'EDIT_TAG', tag})}
                    disabled={tag.system}
                    circular
                    inverted
                  />{' '}
                  <Icon
                    name="remove"
                    color="red"
                    size="small"
                    title={Translate.string('Delete tag')}
                    onClick={() => dispatch({type: 'DELETE_TAG', tag})}
                    disabled={tag.system}
                    circular
                    inverted
                  />
                </span>
              }
            >
              <Translate>
                System tags are managed by the editing workflow service and cannot be modified.
              </Translate>
            </Popup>
          </div>
        </Segment>
      ))}
      {tags.length === 0 && (
        <Message info>
          <Translate>There are no tags defined for this event</Translate>
        </Message>
      )}
      <Button
        onClick={() => dispatch({type: 'ADD_TAG'})}
        disabled={!!operation}
        floated="right"
        icon
        primary
      >
        <Icon name="plus" /> <Translate>Add new tag</Translate>
      </Button>
      {['add', 'edit'].includes(operation) && (
        <TagModal
          header={
            operation === 'edit'
              ? Translate.string('Edit tag')
              : Translate.string('Create a new tag')
          }
          onSubmit={async (formData, form) => {
            if (operation === 'edit') {
              return await editTag(currentTag.id, getChangedValues(formData, form));
            } else {
              return await createTag(formData);
            }
          }}
          tag={currentTag}
          onClose={() => dispatch({type: 'CLEAR'})}
        />
      )}
      <RequestConfirmDelete
        onClose={() => dispatch({type: 'CLEAR'})}
        requestFunc={() => deleteTag(currentTag.id)}
        open={operation === 'delete'}
      >
        {currentTag && (
          <Translate>
            Are you sure you want to delete the tag{' '}
            <Param name="tag" value={currentTag.verboseTitle} wrapper={<strong />} />?
          </Translate>
        )}
      </RequestConfirmDelete>
    </div>
  );
}

TagManager.propTypes = {
  eventId: PropTypes.number.isRequired,
};
