// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionDisplayURL from 'indico-url:contributions.display_contribution';
import assignMyselfURL from 'indico-url:event_editing.api_assign_editable_self';
import unassignEditorURL from 'indico-url:event_editing.api_unassign_editable';

import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Message, Icon} from 'semantic-ui-react';

import {MathJax} from 'indico/react/components';
import {Param, Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {loadTimeline} from './actions';
import DeleteEditable from './DeleteEditable';
import {getDetails, isTimelineOutdated} from './selectors';

export default function TimelineHeader({children, contribution, state, submitter, eventId}) {
  const {
    canAssignSelf,
    canUnassign,
    canPerformEditorActions,
    type,
    editor,
    editingEnabled,
    reviewConditionsValid,
  } = useSelector(getDetails);
  const isOutdated = useSelector(isTimelineOutdated);
  const dispatch = useDispatch();

  const unassignEditor = async () => {
    try {
      await indicoAxios.delete(
        unassignEditorURL({event_id: eventId, contrib_id: contribution.id, type})
      );
    } catch (error) {
      return handleAxiosError(error);
    }
    dispatch(loadTimeline());
  };

  const assignMyself = async () => {
    try {
      await indicoAxios.put(
        assignMyselfURL({event_id: eventId, contrib_id: contribution.id, type})
      );
    } catch (error) {
      return handleAxiosError(error);
    }
    dispatch(loadTimeline());
  };

  return (
    <>
      <div className="submission-title flexrow">
        <MathJax>
          <h3>
            {contribution.title} <span className="submission-id">#{contribution.friendlyId}</span>
            {contribution.code && <span className="submission-code">{contribution.code}</span>}
          </h3>
        </MathJax>
        <div style={{marginLeft: 'auto'}}>
          <DeleteEditable />
        </div>
      </div>
      <div className="editable-public">
        <div className="review-summary flexrow f-a-center">
          <div className="review-summary-badge">
            {reviewConditionsValid ? (
              <div className={`i-tag ${state.cssClass}`}>{state.title}</div>
            ) : (
              <div className="i-tag">
                <Translate>Not Ready</Translate>
              </div>
            )}
          </div>
          <div className="review-summary-content f-self-stretch">
            <div>
              <Translate>
                <Param name="submitterName" value={submitter.fullName} wrapper={<strong />} />{' '}
                submitted for the contribution{' '}
                <Param
                  name="contributionLink"
                  value={contribution.title}
                  wrapper={
                    <a
                      href={contributionDisplayURL({
                        event_id: eventId,
                        contrib_id: contribution.id,
                      })}
                    />
                  }
                />
              </Translate>
              <br />
              {editor ? (
                <>
                  <Translate>
                    <Param name="editorName" value={editor.fullName} wrapper={<strong />} /> is the
                    assigned editor
                  </Translate>
                  {canUnassign && !isOutdated && (
                    <>
                      {' ('}
                      <a onClick={unassignEditor}>
                        <Translate>unassign</Translate>
                      </a>
                      )
                    </>
                  )}
                </>
              ) : (
                <>
                  <Translate>No editor assigned</Translate>
                  {canAssignSelf && !isOutdated && (
                    <>
                      {' ('}
                      <a onClick={assignMyself}>
                        <Translate>assign myself</Translate>
                      </a>
                      )
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
        {!reviewConditionsValid && (
          <Message warning>
            <Icon name="warning sign" />
            <Translate>This editable is not fulfilling reviewing conditions.</Translate>
          </Message>
        )}
        {!editingEnabled && (
          <Message warning>
            <Icon name="warning sign" />
            <Translate>The Editing period hasn't started yet.</Translate>
            {canPerformEditorActions && (
              <>
                {' '}
                <Translate>Since you are a manager you can edit anyway.</Translate>
              </>
            )}
          </Message>
        )}
        {editingEnabled && canAssignSelf && (
          <Message warning>
            <Icon name="warning sign" />
            <Translate>This editable is not currently assigned to you.</Translate>
          </Message>
        )}
        {children && <div className="review-item-content">{children}</div>}
      </div>
    </>
  );
}

TimelineHeader.propTypes = {
  contribution: PropTypes.shape({
    id: PropTypes.number.isRequired,
    friendlyId: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    code: PropTypes.string.isRequired,
  }).isRequired,
  state: PropTypes.shape({
    cssClass: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  }).isRequired,
  submitter: PropTypes.shape({
    fullName: PropTypes.string.isRequired,
  }).isRequired,
  eventId: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
};
