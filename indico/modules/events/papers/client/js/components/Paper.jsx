// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useEffect} from 'react';
import PropTypes from 'prop-types';
import {useDispatch, useSelector} from 'react-redux';
import {Loader} from 'semantic-ui-react';

import TimelineHeader from 'indico/modules/events/reviewing/components/TimelineHeader';
import TimelineContent from 'indico/modules/events/reviewing/components/TimelineContent';
import {fetchPaperDetails} from '../actions';
import {getPaperDetails, isFetchingInitialPaperDetails} from '../selectors';
import PaperDecisionForm from './PaperDecisionForm';
import PaperContent from './PaperContent';
import TimelineItem from './TimelineItem';

export default function Paper({eventId, contributionId}) {
  const dispatch = useDispatch();
  const paper = useSelector(getPaperDetails);
  const isInitialPaperDetailsLoading = useSelector(isFetchingInitialPaperDetails);

  useEffect(() => {
    dispatch(fetchPaperDetails(eventId, contributionId));
  }, [dispatch, contributionId, eventId]);

  if (isInitialPaperDetailsLoading) {
    return <Loader active />;
  } else if (!paper) {
    return null;
  }

  const {
    contribution,
    state,
    lastRevision: {submitter},
    isInFinalState,
  } = paper;

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
      <TimelineContent
        itemComponent={TimelineItem}
        revisions={paper.revisions}
        state={{...state, isFinal: isInFinalState}}
      />
      <PaperDecisionForm />
    </>
  );
}

Paper.propTypes = {
  eventId: PropTypes.number.isRequired,
  contributionId: PropTypes.number.isRequired,
};
