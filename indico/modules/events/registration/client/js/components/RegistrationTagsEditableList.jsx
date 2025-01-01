// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import registrationTagAssign from 'indico-url:event_registration.api_registration_tags_assign';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Icon, Divider, Header, Label} from 'semantic-ui-react';

import {IButton, PopoverDropdownMenu} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './RegistrationTagsEditableList.module.scss';

export default function RegistrationTagsEditableList({
  eventId,
  regformId,
  registrationId,
  assignedTags,
  allTags,
}) {
  const [tags, setTags] = useState(assignedTags);
  const [open, setOpen] = useState(false);
  const unassignedTags = _.differenceBy(allTags, tags, 'id');

  async function editRegistrationTags({add = [], remove = []}) {
    try {
      await indicoAxios.post(registrationTagAssign({reg_form_id: regformId, event_id: eventId}), {
        registration_id: [registrationId],
        add,
        remove,
      });
    } catch (error) {
      return handleAxiosError(error);
    }
  }

  function onRemove(tag) {
    setTags(tags.filter(t => t.id !== tag.id));
    editRegistrationTags({remove: [tag.id]});
  }

  function onAdd(tag) {
    const newTags = _.sortBy([...tags, tag], [t => t.title.toLowerCase()], 'title');
    setTags(newTags);
    if (newTags.length === allTags.length) {
      setOpen(false);
    }
    editRegistrationTags({add: [tag.id]});
  }

  const trigger = (
    <IButton disabled={unassignedTags.length === 0}>
      <Translate>Add</Translate>
      <Icon name="caret down" style={{marginRight: 0}} />
    </IButton>
  );

  return (
    <>
      <div className="icon icon-tag" />
      <div className="text">
        <div className="label">
          <Translate>Tags</Translate>
        </div>
        <div
          styleName="removable-tags-container"
          style={{marginTop: tags.length === 0 ? '0' : '3px'}}
        >
          {tags.length === 0 ? (
            <Translate>No tags assigned.</Translate>
          ) : (
            tags.map(tag => (
              <Label
                size="medium"
                key={tag.title}
                styleName="registration-tag removable"
                color={tag.color}
              >
                {tag.title}
                <Icon name="close" onClick={() => onRemove(tag)} />
              </Label>
            ))
          )}
        </div>
      </div>
      <div className="toolbar">
        {unassignedTags.length === 0 ? (
          trigger
        ) : (
          <PopoverDropdownMenu
            onOpen={() => setOpen(true)}
            onClose={() => setOpen(false)}
            trigger={trigger}
            open={open}
            placement="right-start"
          >
            <Header size="small" textAlign="center">
              <Translate>Add tags</Translate>
            </Header>
            <Divider style={{margin: 0}} />
            <div styleName="selectable-tags-container">
              {unassignedTags.map(tag => (
                <div key={tag.title} onClick={() => onAdd(tag)}>
                  <Label styleName="registration-tag selectable" color={tag.color}>
                    {tag.title}
                  </Label>
                </div>
              ))}
            </div>
          </PopoverDropdownMenu>
        )}
      </div>
    </>
  );
}

RegistrationTagsEditableList.propTypes = {
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
  registrationId: PropTypes.number.isRequired,
  assignedTags: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      color: PropTypes.string.isRequired,
    })
  ).isRequired,
  allTags: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      color: PropTypes.string.isRequired,
    })
  ).isRequired,
};
