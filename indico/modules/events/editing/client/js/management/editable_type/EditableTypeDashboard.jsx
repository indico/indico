// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
/* global ajaxDialog:false */

import dashboardURL from 'indico-url:event_editing.dashboard';
import manageEditableTypeListURL from 'indico-url:event_editing.manage_editable_type_list';
import manageFileTypesURL from 'indico-url:event_editing.manage_file_types';
import manageReviewConditionsURL from 'indico-url:event_editing.manage_review_conditions';
import selfAssignURL from 'indico-url:event_editing.api_self_assign_enabled';
import enableSubmissionURL from 'indico-url:event_editing.api_submission_enabled';
import enableEditingURL from 'indico-url:event_editing.api_editing_enabled';
import contactEditingTeamURL from 'indico-url:event_editing.contact_team';

import React, {useState} from 'react';
import {useParams, Link} from 'react-router-dom';
import {Checkbox, Loader} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {ManagementPageSubTitle, ManagementPageBackButton} from 'indico/react/components';
import {useNumericParam} from 'indico/react/util/routing';
import {useTogglableValue} from 'indico/react/hooks';
import {EditableTypeTitles} from '../../models';
import Section from '../Section';
import TeamManager from './TeamManager';
import NextEditable from './NextEditable';

import './EditableTypeDashboard.module.scss';

export default function EditableTypeDashboard() {
  const eventId = useNumericParam('confId');
  const {type} = useParams();
  const [editorManagerVisible, setEditorManagerVisible] = useState(false);
  const [selfAssignModalVisible, setSelfAssignModalVisible] = useState(false);

  const [
    selfAssignEnabled,
    toggleSelfAssign,
    selfAssignLoading,
    selfAssignSaving,
  ] = useTogglableValue(selfAssignURL({confId: eventId, type}));

  const [submissionEnabled, toggleSubmission, submissionLoading] = useTogglableValue(
    enableSubmissionURL({confId: eventId, type})
  );

  const [editingEnabled, toggleEditing, editingLoading] = useTogglableValue(
    enableEditingURL({confId: eventId, type})
  );

  const contactEditingTeam = () => {
    ajaxDialog({
      url: contactEditingTeamURL({confId: eventId, type}),
      title: Translate.string('Send emails to the editing team'),
    });
  };

  return (
    <>
      <ManagementPageSubTitle title={EditableTypeTitles[type]} />
      <ManagementPageBackButton url={dashboardURL({confId: eventId})} />
      {selfAssignLoading || submissionLoading || editingLoading ? (
        <Loader active />
      ) : (
        <>
          <div className="action-box">
            <Section
              icon="file"
              label={
                submissionEnabled
                  ? Translate.string('Submission is open')
                  : Translate.string('Submission is not open')
              }
              description={Translate.string('Toggle whether users can submit new editables')}
            >
              <a className="i-button highlight icon-list" onClick={toggleSubmission}>
                {submissionEnabled ? Translate.string('Close now') : Translate.string('Start now')}
              </a>
            </Section>
            <Section
              icon="edit"
              label={
                editingEnabled
                  ? Translate.string('Editing is open')
                  : Translate.string('Editing is not open')
              }
              description={Translate.string('Toggle whether editors can review submissions')}
            >
              <a className="i-button highlight icon-list" onClick={toggleEditing}>
                {editingEnabled ? Translate.string('Close now') : Translate.string('Start now')}
              </a>
            </Section>
          </div>
          <div className="action-box">
            <Section
              icon="file"
              label={Translate.string('File types')}
              description={Translate.string('Configure file types')}
            >
              <Link
                className="i-button icon-settings"
                to={manageFileTypesURL({confId: eventId, type})}
              >
                <Translate>Configure</Translate>
              </Link>
            </Section>
            <Section
              icon="equalizer"
              label={Translate.string('Ready for review conditions')}
              description={Translate.string('Configure conditions for reviewing')}
            >
              <Link
                className="i-button icon-settings"
                to={manageReviewConditionsURL({confId: eventId, type})}
              >
                <Translate>Configure</Translate>
              </Link>
            </Section>
            <Section
              icon="users"
              label={Translate.string('Editing team')}
              description={Translate.string('Configure editing team')}
            >
              <a className="i-button icon-mail" onClick={contactEditingTeam}>
                <Translate>Contact</Translate>
              </a>
              <a className="i-button icon-users" onClick={() => setEditorManagerVisible(true)}>
                <Translate>Manage team</Translate>
              </a>
              {editorManagerVisible && (
                <TeamManager editableType={type} onClose={() => setEditorManagerVisible(false)} />
              )}
            </Section>
            <Section
              icon="copy1"
              label={Translate.string('Editable assignment')}
              description={Translate.string('Assign editors')}
            >
              <Checkbox
                styleName="toolbar-checkbox"
                toggle
                checked={selfAssignEnabled}
                onClick={!selfAssignSaving ? toggleSelfAssign : null}
                label={Translate.string('Allow editors to self-assign editables')}
              />
              <Link
                className="i-button icon-settings"
                to={manageEditableTypeListURL({confId: eventId, type})}
              >
                <Translate>List</Translate>
              </Link>
              <a
                className="i-button icon-arrow-right-sparse"
                onClick={() => setSelfAssignModalVisible(true)}
              >
                <Translate>Get next editable</Translate>
              </a>
              {selfAssignModalVisible && (
                <NextEditable
                  eventId={eventId}
                  editableType={type}
                  onClose={() => setSelfAssignModalVisible(false)}
                />
              )}
            </Section>
          </div>
        </>
      )}
    </>
  );
}
