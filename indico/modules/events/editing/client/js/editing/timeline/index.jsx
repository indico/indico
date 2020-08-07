// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect, useRef, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Loader, Message} from 'semantic-ui-react';
import _ from 'lodash';

import TimelineHeader from 'indico/modules/events/editing/editing/timeline/TimelineHeader';
import TimelineContent from 'indico/modules/events/reviewing/components/TimelineContent';
import {indicoAxios} from 'indico/utils/axios';
import {Param, Translate} from 'indico/react/i18n';
import SubmitRevision from './SubmitRevision';

import * as actions from './actions';
import * as selectors from './selectors';
import TimelineItem from './TimelineItem';
import FileDisplay from './FileDisplay';

const POLLING_SECONDS = 10;

export default function Timeline() {
  const dispatch = useDispatch();
  const details = useSelector(selectors.getDetails);
  const isInitialEditableDetailsLoading = useSelector(selectors.isInitialEditableDetailsLoading);
  const needsSubmitterChanges = useSelector(selectors.needsSubmitterChanges);
  const canPerformSubmitterActions = useSelector(selectors.canPerformSubmitterActions);
  const lastRevision = useSelector(selectors.getLastRevision);
  const timelineBlocks = useSelector(selectors.getTimelineBlocks);
  const {eventId, contributionId, editableType, fileTypes, editableDetailsURL} = useSelector(
    selectors.getStaticData
  );
  const [isOutdated, setIsOutdated] = useState(false);
  const newDetails = useRef(null);

  useEffect(() => {
    dispatch(
      actions.loadTimeline(data => {
        newDetails.current = data;
        return data;
      })
    );
  }, [editableDetailsURL, contributionId, eventId, editableType, dispatch]);

  useEffect(() => {
    const task = setInterval(async () => {
      const resp = await indicoAxios.get(editableDetailsURL);
      if (!_.isEqual(newDetails.current, resp.data)) {
        newDetails.current = resp.data;
        setIsOutdated(true);
      }
    }, POLLING_SECONDS * 1000);
    return () => {
      clearInterval(task);
    };
  }, [timelineBlocks, editableDetailsURL]);

  const refresh = () => {
    dispatch({type: actions.SET_DETAILS, data: newDetails.current});
    setIsOutdated(false);
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
        submitter={timelineBlocks[0].submitter}
        eventId={eventId}
      >
        <FileDisplay
          fileTypes={fileTypes}
          files={lastRevision.files}
          downloadURL={lastRevision.downloadFilesURL}
          tags={lastRevision.tags}
        />
      </TimelineHeader>
      <TimelineContent blocks={timelineBlocks} itemComponent={TimelineItem} />
      {canPerformSubmitterActions && needsSubmitterChanges && <SubmitRevision />}
    </>
  );
}
