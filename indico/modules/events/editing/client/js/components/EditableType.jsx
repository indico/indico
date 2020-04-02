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
import Section from './Section';

import './EditableType.module.scss';

export default function EditableType({eventId, editableType}) {
  return (
    <>
      <div className="action-box">
        <Section
          icon="file"
          label={Translate.string('Submission is not open yet')}
          description={Translate.string('Start now')}
        >
          <a className="i-button highlight icon-list">
            <Translate>Start now</Translate>
          </a>
        </Section>
        <Section
          icon="edit"
          label={Translate.string('Editing is not open yet')}
          description={Translate.string('Start now')}
        >
          <a className="i-button highlight icon-list">
            <Translate>Start now</Translate>
          </a>
        </Section>
      </div>
      <div className="action-box">
        <Section
          icon="file"
          label={Translate.string('File types')}
          description={Translate.string('Configure file types')}
        >
          <a
            className="i-button icon-settings"
            href={manageFileTypesURL({confId: eventId, type: editableType})}
          >
            <Translate>Configure</Translate>
          </a>
        </Section>
        <Section
          icon="equalizer"
          label={Translate.string('Ready for review conditions')}
          description={Translate.string('Configure conditions for reviewing')}
        >
          <a
            className="i-button icon-settings"
            href={manageReviewConditionsURL({confId: eventId, type: editableType})}
          >
            <Translate>Configure</Translate>
          </a>
        </Section>
        <Section
          icon="users"
          label={Translate.string('Editing team')}
          description={Translate.string('Configure editing team')}
        >
          <a className="i-button icon-mail">
            <Translate>Contact</Translate>
          </a>
          <a className="i-button icon-users">
            <Translate>Manage team</Translate>
          </a>
        </Section>
        <Section
          icon="copy1"
          label={Translate.string('Editable assignment')}
          description={Translate.string('Assign editors')}
        >
          <Checkbox styleName="toolbar-checkbox" toggle />
          <span styleName="toolbar-label">
            <Translate>Allow editors to self-assign editables</Translate>
          </span>
          <a className="i-button icon-settings">
            <Translate>Assign</Translate>
          </a>
        </Section>
      </div>
    </>
  );
}

EditableType.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.keys(EditableTypeTitles)).isRequired,
};
