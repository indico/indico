// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import tagsURL from 'indico-url:event_editing.api_tags';
import createTagURL from 'indico-url:event_editing.api_create_tag';
import editTagURL from 'indico-url:event_editing.api_edit_tag';

import React, {useReducer} from 'react';
import PropTypes from 'prop-types';
import {Button, Icon, Label, Loader, Message, Segment} from 'semantic-ui-react';

import {Param, Translate} from 'indico/react/i18n';
import {getChangedValues, handleSubmissionError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {handleAxiosError, indicoAxios} from 'indico/utils/axios';
import RequestConfirm from './RequestConfirm';
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
  const {data, loading: isLoadingTags, reFetch, lastData} = useIndicoAxios({
    url: tagsURL({confId: eventId}),
    camelize: true,
    trigger: eventId,
  });

  const createTag = async formData => {
    try {
      await indicoAxios.post(createTagURL({confId: eventId}), formData);
      reFetch();
    } catch (e) {
      return handleSubmissionError(e);
    }
  };

  const editTag = async (tagId, tagData) => {
    const url = editTagURL({confId: eventId, tag_id: tagId});

    try {
      await indicoAxios.patch(url, tagData);
      reFetch();
    } catch (e) {
      return handleSubmissionError(e);
    }
  };

  const deleteTag = async tagId => {
    const url = editTagURL({confId: eventId, tag_id: tagId});

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
            <Icon
              name="pencil"
              color="grey"
              size="small"
              onClick={() => dispatch({type: 'EDIT_TAG', tag})}
              circular
              inverted
            />
            <Icon
              name="remove"
              color="red"
              size="small"
              onClick={() => dispatch({type: 'DELETE_TAG', tag})}
              circular
              inverted
            />
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
          initialValues={currentTag}
          onClose={() => dispatch({type: 'CLEAR'})}
        />
      )}
      {operation === 'delete' && (
        <RequestConfirm
          header={Translate.string('Delete tag')}
          confirmText={Translate.string('Yes')}
          cancelText={Translate.string('No')}
          onClose={() => dispatch({type: 'CLEAR'})}
          content={
            <div className="content">
              <Translate>
                Are you sure you want to delete the tag{' '}
                <Param name="tag" value={currentTag.verboseTitle} wrapper={<strong />} />?
              </Translate>
            </div>
          }
          requestFunc={() => deleteTag(currentTag.id)}
          open
        />
      )}
    </div>
  );
}

TagManager.propTypes = {
  eventId: PropTypes.number.isRequired,
};
