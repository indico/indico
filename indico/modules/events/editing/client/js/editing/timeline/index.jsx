// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Loader, Message} from 'semantic-ui-react';

import TimelineHeader from 'indico/modules/events/editing/editing/timeline/TimelineHeader';
import TimelineContent from 'indico/modules/events/reviewing/components/TimelineContent';
import {Param, Translate} from 'indico/react/i18n';

import * as actions from './actions';
import FileDisplay from './FileDisplay';
import * as selectors from './selectors';
import SubmitRevision from './SubmitRevision';
import TimelineItem from './TimelineItem';

const POLLING_SECONDS = 10;

export default function Timeline() {
  const dispatch = useDispatch();
  const details = useSelector(selectors.getDetails);
  const isInitialEditableDetailsLoading = useSelector(selectors.isInitialEditableDetailsLoading);
  const needsSubmitterChanges = useSelector(selectors.needsSubmitterChanges);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const lastRevision = useSelector(selectors.getLastRevision);
  const lastRevisionWithFiles = useSelector(selectors.getLastRevisionWithFiles);
  const timelineBlocks = useSelector(selectors.getTimelineBlocks);
  const {eventId, contributionId, editableType, fileTypes} = useSelector(selectors.getStaticData);
  const isOutdated = useSelector(selectors.isTimelineOutdated);

  useEffect(() => {
    dispatch(actions.loadTimeline());
  }, [contributionId, eventId, editableType, dispatch]);

  useEffect(() => {
    const task = setInterval(async () => {
      dispatch(actions.checkTimelineUpdates());
    }, POLLING_SECONDS * 1000);
    return () => {
      clearInterval(task);
    };
  }, [dispatch]);

  useEffect(() => {
    if (details) {
      localStorage.setItem(`editable-${details.id}-last-update`, details.lastUpdateDt);
    }
  }, [details]);

  const refresh = () => {
    dispatch(actions.useUpdatedTimeline());
  };

  if (isInitialEditableDetailsLoading) {
    return <Loader active />;
  } else if (!details) {
    return null;
  }

  return (
    <>
      {isOutdated && (
        <Message
          warning
          header={Translate.string('This revision has been updated')}
          content={
            <Translate>
              <Param name="link" wrapper={<a onClick={refresh} />}>
                Click here to refresh
              </Param>{' '}
              and see the most recent version.
            </Translate>
          }
        />
      )}
      <TimelineHeader
        contribution={details.contribution}
        state={details.state}
        submitter={timelineBlocks[0].user}
        eventId={eventId}
      >
        {details.hasPublishedRevision && (
          <FileDisplay
            fileTypes={fileTypes}
            files={lastRevisionWithFiles.files}
            downloadURL={lastRevisionWithFiles.downloadFilesURL}
            tags={lastRevision.tags}
          />
        )}
      </TimelineHeader>
      <TimelineContent blocks={timelineBlocks} itemComponent={TimelineItem} />
      {canPerformSubmitterActions && needsSubmitterChanges && <SubmitRevision />}
    </>
  );
}
