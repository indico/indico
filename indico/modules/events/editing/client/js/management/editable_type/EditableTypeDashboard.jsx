// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global ajaxDialog:false */

import anonymousTeamURL from 'indico-url:event_editing.api_anonymous_team';
import contribsWithNoEditablesURL from 'indico-url:event_editing.api_contribs_with_no_editables';
import enableEditingURL from 'indico-url:event_editing.api_editing_enabled';
import emailMetadataURL from 'indico-url:event_editing.api_email_not_submitted_metadata';
import emailPreviewURL from 'indico-url:event_editing.api_email_not_submitted_preview';
import emailSendURL from 'indico-url:event_editing.api_email_not_submitted_send';
import selfAssignURL from 'indico-url:event_editing.api_self_assign_enabled';
import enableSubmissionURL from 'indico-url:event_editing.api_submission_enabled';
import contactEditingTeamURL from 'indico-url:event_editing.contact_team';
import dashboardURL from 'indico-url:event_editing.dashboard';
import manageEditableTypeListURL from 'indico-url:event_editing.manage_editable_type_list';
import manageFileTypesURL from 'indico-url:event_editing.manage_file_types';
import manageReviewConditionsURL from 'indico-url:event_editing.manage_review_conditions';

import React, {useState} from 'react';
import {useParams, Link} from 'react-router-dom';
import {Loader} from 'semantic-ui-react';

import {EmailContribAbstractRolesButton} from 'indico/modules/events/persons/EmailContribAbstractRolesButton';
import {ManagementPageSubTitle, ManagementPageBackButton, Checkbox} from 'indico/react/components';
import {useIndicoAxios, useTogglableValue} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {useNumericParam} from 'indico/react/util/routing';

import {EditableTypeTitles, GetNextEditableTitles} from '../../models';
import Section from '../Section';

import NextEditable from './NextEditable';
import TeamManager from './TeamManager';

import './EditableTypeDashboard.module.scss';

export default function EditableTypeDashboard() {
  const eventId = useNumericParam('event_id');
  const {type} = useParams();
  const [editorManagerVisible, setEditorManagerVisible] = useState(false);
  const [selfAssignModalVisible, setSelfAssignModalVisible] = useState(false);

  const [
    selfAssignEnabled,
    toggleSelfAssign,
    selfAssignLoading,
    selfAssignSaving,
  ] = useTogglableValue(selfAssignURL({event_id: eventId, type}));

  const [
    anonymousTeamEnabled,
    toggleAnonymousTeam,
    anonymousTeamLoading,
    anonymousTeamSaving,
  ] = useTogglableValue(anonymousTeamURL({event_id: eventId, type}));

  const [submissionEnabled, toggleSubmission, submissionLoading] = useTogglableValue(
    enableSubmissionURL({event_id: eventId, type})
  );

  const [editingEnabled, toggleEditing, editingLoading] = useTogglableValue(
    enableEditingURL({event_id: eventId, type})
  );

  const contactEditingTeam = () => {
    ajaxDialog({
      url: contactEditingTeamURL({event_id: eventId, type}),
      title: Translate.string('Send emails to the editing team'),
    });
  };

  const editorAssignmentDescription = {
    paper: Translate.string('Assign an editor to papers'),
    poster: Translate.string('Assign an editor to posters'),
    slides: Translate.string('Assign an editor to slides'),
  }[type];

  const {data} = useIndicoAxios(contribsWithNoEditablesURL({event_id: eventId, type}));
  const numEditables = data?.count || 0;

  return (
    <>
      <ManagementPageSubTitle title={EditableTypeTitles[type]} />
      <ManagementPageBackButton url={dashboardURL({event_id: eventId})} />
      {selfAssignLoading || anonymousTeamLoading || submissionLoading || editingLoading ? (
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
              <button className="i-button highlight" onClick={toggleSubmission} type="button">
                {submissionEnabled ? Translate.string('Close now') : Translate.string('Start now')}
              </button>
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
              <button className="i-button highlight" onClick={toggleEditing} type="button">
                {editingEnabled ? Translate.string('Close now') : Translate.string('Start now')}
              </button>
            </Section>
            <Section
              icon="bell"
              label={Translate.string('Remind submitters')}
              description={Translate.string(
                'Send an email to authors who have not submitted any files of this editable type'
              )}
            >
              <span className="i-label" title={Translate.string('Contributions without editables')}>
                {numEditables}
              </span>
              <EmailContribAbstractRolesButton
                objectContext="contributions"
                metadataURL={emailMetadataURL({event_id: eventId, type})}
                previewURL={emailPreviewURL({event_id: eventId, type})}
                sendURL={emailSendURL({event_id: eventId, type})}
                className={numEditables > 0 ? '' : 'disabled'}
              />
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
                to={manageFileTypesURL({event_id: eventId, type})}
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
                to={manageReviewConditionsURL({event_id: eventId, type})}
              >
                <Translate>Configure</Translate>
              </Link>
            </Section>
            <Section
              icon="users"
              label={Translate.string('Editing team')}
              description={Translate.string('Configure editing team')}
            >
              <Checkbox
                styleName="toolbar-checkbox"
                showAsToggle
                checked={anonymousTeamEnabled}
                onChange={!anonymousTeamSaving ? toggleAnonymousTeam : null}
                label={Translate.string('Keep editing team members anonymous')}
              />
              <button className="i-button icon-mail" onClick={contactEditingTeam} type="button">
                <Translate>Contact</Translate>
              </button>
              <button
                className="i-button icon-users"
                onClick={() => setEditorManagerVisible(true)}
                type="button"
              >
                <Translate>Manage team</Translate>
              </button>
              {editorManagerVisible && (
                <TeamManager editableType={type} onClose={() => setEditorManagerVisible(false)} />
              )}
            </Section>
            <Section
              icon="copy1"
              label={Translate.string('Editor assignment')}
              description={editorAssignmentDescription}
            >
              <Checkbox
                styleName="toolbar-checkbox"
                showAsToggle
                checked={selfAssignEnabled}
                onChange={!selfAssignSaving ? toggleSelfAssign : null}
                label={Translate.string('Allow editors to self-assign editables')}
              />
              <Link
                className="i-button icon-list"
                to={manageEditableTypeListURL({event_id: eventId, type})}
              >
                <Translate>List</Translate>
              </Link>
              <a
                className="i-button icon-arrow-right-sparse"
                onClick={() => setSelfAssignModalVisible(true)}
              >
                {GetNextEditableTitles[type]}
              </a>
              {selfAssignModalVisible && (
                <NextEditable
                  eventId={eventId}
                  editableType={type}
                  onClose={() => setSelfAssignModalVisible(false)}
                  management
                />
              )}
            </Section>
          </div>
        </>
      )}
    </>
  );
}
