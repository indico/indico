// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import manageFileTypesURL from 'indico-url:event_editing.manage_file_types';
import manageReviewConditionsURL from 'indico-url:event_editing.manage_review_conditions';

import React from 'react';
import PropTypes from 'prop-types';
import {Checkbox} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {EditableTypeTitles} from '../models';

import './EditableType.module.scss';

export default function EditableType({eventId, editableType}) {
  return (
    <>
      <div className="action-box">
        <div className="section">
          <span className="icon icon-file" />
          <div className="text">
            <div className="label">
              <Translate>Submission is not open yet</Translate>
            </div>
            <Translate>Start now</Translate>
          </div>
          <div className="toolbar">
            <a className="i-button highlight icon-list">
              <Translate>Start now</Translate>
            </a>
          </div>
        </div>
        <div className="section">
          <span className="icon icon-edit" />
          <div className="text">
            <div className="label">
              <Translate>Editing is not open yet</Translate>
            </div>
            <Translate>Start now</Translate>
          </div>
          <div className="toolbar">
            <a className="i-button highlight icon-list">
              <Translate>Start now</Translate>
            </a>
          </div>
        </div>
      </div>
      <div className="action-box">
        <div className="section">
          <span className="icon icon-file" />
          <div className="text">
            <div className="label">
              <Translate>File types</Translate>
            </div>
            <Translate>Configure file types</Translate>
          </div>
          <div className="toolbar">
            <a
              className="i-button icon-settings"
              href={manageFileTypesURL({confId: eventId, type: editableType})}
            >
              <Translate>Configure</Translate>
            </a>
          </div>
        </div>
        <div className="section">
          <span className="icon icon-equalizer" />
          <div className="text">
            <div className="label">
              <Translate>Ready for review conditions</Translate>
            </div>
            <Translate>Configure conditions for reviewing</Translate>
          </div>
          <div className="toolbar">
            <a
              className="i-button icon-settings"
              href={manageReviewConditionsURL({confId: eventId, type: editableType})}
            >
              <Translate>Configure</Translate>
            </a>
          </div>
        </div>
        <div className="section">
          <span className="icon icon-users" />
          <div className="text">
            <div className="label">
              <Translate>Editing team</Translate>
            </div>
            <Translate>Configure editing team</Translate>
          </div>
          <div className="toolbar">
            <a className="i-button icon-mail">
              <Translate>Contact</Translate>
            </a>
            <a className="i-button icon-users">
              <Translate>Manage team</Translate>
            </a>
          </div>
        </div>
        <div className="section">
          <span className="icon icon-copy1" />
          <div className="text">
            <div className="label">
              <Translate>Editable assignment</Translate>
            </div>
            <Translate>Assign editors</Translate>
          </div>
          <div className="toolbar">
            <Checkbox styleName="toolbar-checkbox" toggle />
            <span styleName="toolbar-label">
              <Translate>Allow editors to self-assign editables</Translate>
            </span>
            <a className="i-button icon-settings">
              <Translate>Assign</Translate>
            </a>
          </div>
        </div>
      </div>
    </>
  );
}

EditableType.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.keys(EditableTypeTitles)).isRequired,
};
