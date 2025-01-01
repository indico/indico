// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import editableDetailsURL from 'indico-url:event_editing.api_editable';
import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableURL from 'indico-url:event_editing.editable';

import PropTypes from 'prop-types';
import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon, Loader, Step} from 'semantic-ui-react';

import EditableSubmissionButton from 'indico/modules/events/editing/editing/EditableSubmissionButton';
import {
  fileTypePropTypes,
  uploadablePropTypes,
} from 'indico/modules/events/editing/editing/timeline/FileManager/util';
import {EditableType} from 'indico/modules/events/editing/models';
import TimelineContent from 'indico/modules/events/reviewing/components/TimelineContent';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate, Param} from 'indico/react/i18n';

import {fetchPaperDetails} from '../actions';
import {PaperState} from '../models';
import {getPaperDetails, isFetchingInitialPaperDetails} from '../selectors';

import PaperContent from './PaperContent';
import PaperDecisionForm from './PaperDecisionForm';
import TimelineHeader from './TimelineHeader';
import TimelineItem from './TimelineItem';

export default function Paper({eventId, contributionId}) {
  const dispatch = useDispatch();
  const paper = useSelector(getPaperDetails);
  const isInitialPaperDetailsLoading = useSelector(isFetchingInitialPaperDetails);
  const {data: fileTypes, loading: isFileTypesLoading} = useIndicoAxios(
    fileTypesURL({event_id: eventId, type: EditableType.paper}),
    {
      unhandledErrors: [404], // if editing module is disabled
      camelize: true,
    }
  );
  const {data: editable, loading: isEditableLoading} = useIndicoAxios(
    editableDetailsURL({
      event_id: eventId,
      contrib_id: contributionId,
      type: EditableType.paper,
    }),
    {
      unhandledErrors: [404, 403], // if there is no editable yet (404) or viewed by a paper reviewer (403)
      camelize: true,
    }
  );

  useEffect(() => {
    dispatch(fetchPaperDetails(eventId, contributionId));
  }, [dispatch, contributionId, eventId]);

  if (isInitialPaperDetailsLoading || isFileTypesLoading || isEditableLoading) {
    return <Loader active />;
  } else if (!paper) {
    return null;
  }

  const {
    contribution,
    lastRevision: {submitter, files},
    revisions,
    state,
    isInFinalState,
    canSubmitProceedings,
    editingEnabled,
    editingOpen,
  } = paper;

  const isEditingEnabled = editingEnabled && editingOpen && !!fileTypes;

  return (
    <>
      <TimelineHeader
        contribution={contribution}
        state={state}
        submitter={submitter}
        eventId={eventId}
      >
        <PaperContent />
      </TimelineHeader>
      {canSubmitProceedings && isEditingEnabled && (
        <PaperSteps
          isInFinalState={isInFinalState}
          isRejected={state.name === PaperState.rejected}
          hasEditable={!!editable}
          fileTypes={fileTypes}
          uploadableFiles={files}
          editableURL={editableURL({
            event_id: eventId,
            contrib_id: contributionId,
            type: EditableType.paper,
          })}
        />
      )}
      <TimelineContent itemComponent={TimelineItem} blocks={revisions} />
      <PaperDecisionForm />
    </>
  );
}

Paper.propTypes = {
  eventId: PropTypes.number.isRequired,
  contributionId: PropTypes.number.isRequired,
};

function PaperSteps({
  isInFinalState,
  isRejected,
  hasEditable,
  // eslint-disable-next-line no-shadow
  editableURL,
  fileTypes,
  uploadableFiles,
}) {
  const {event, contribution} = useSelector(getPaperDetails);

  return (
    <Step.Group fluid>
      <Step active={!isInFinalState} completed={isInFinalState}>
        <Icon name="copy outline" />
        <Step.Content>
          <Step.Title>
            <Translate>Peer Reviewing</Translate>
          </Step.Title>
          <Step.Description style={{marginBottom: 0}}>
            {isInFinalState ? (
              <Translate>The paper was reviewed</Translate>
            ) : (
              <Translate>Your paper is under review</Translate>
            )}
          </Step.Description>
        </Step.Content>
      </Step>
      <Step active={isInFinalState} completed={hasEditable} disabled={isRejected}>
        <Icon name="pencil alternate" />
        <Step.Content>
          <Step.Title>
            {hasEditable || !isInFinalState || isRejected ? (
              <Translate>Submit for Editing</Translate>
            ) : (
              <EditableSubmissionButton
                eventId={event.id}
                contributionId={contribution.id}
                contributionCode={contribution.code}
                fileTypes={{[EditableType.paper]: fileTypes}}
                uploadableFiles={uploadableFiles.map(({id, ...rest}) => ({...rest, paperId: id}))}
                text={Translate.string('Submit for editing')}
              />
            )}
          </Step.Title>
          {hasEditable && (
            <Step.Description style={{marginBottom: 0}}>
              <Translate>
                The paper was{' '}
                <Param name="url" wrapper={<a href={editableURL} />}>
                  submitted
                </Param>{' '}
                for editing
              </Translate>
            </Step.Description>
          )}
        </Step.Content>
      </Step>
    </Step.Group>
  );
}

PaperSteps.propTypes = {
  isInFinalState: PropTypes.bool.isRequired,
  isRejected: PropTypes.bool.isRequired,
  hasEditable: PropTypes.bool.isRequired,
  editableURL: PropTypes.string,
  fileTypes: PropTypes.arrayOf(PropTypes.shape(fileTypePropTypes)).isRequired,
  uploadableFiles: PropTypes.arrayOf(PropTypes.shape(uploadablePropTypes)),
};

PaperSteps.defaultProps = {
  uploadableFiles: [],
  editableURL: undefined,
};
