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

import {fetchPaperDetails, fetchPaperPermissions} from '../actions';
import {getPaperDetails, isFetchingPaperDetails, isFetchingPaperPermissions} from '../selectors';
import PaperInfo from './PaperInfo';
import PaperTimeline from './PaperTimeline';
import PaperDecisionForm from './PaperDecisionForm';

export default function Paper({eventId, contributionId}) {
  const dispatch = useDispatch();
  const paper = useSelector(getPaperDetails);
  const isFetchingDetails = useSelector(isFetchingPaperDetails);
  const isFetchingPermissions = useSelector(isFetchingPaperPermissions);

  useEffect(() => {
    dispatch(fetchPaperDetails(eventId, contributionId));
    dispatch(fetchPaperPermissions(eventId, contributionId));
  }, [dispatch, contributionId, eventId]);

  if (isFetchingDetails || isFetchingPermissions) {
    return <Loader active />;
  } else if (!paper) {
    return null;
  }

  return (
    <>
      <PaperInfo />
      <PaperTimeline />
      <PaperDecisionForm />
    </>
  );
}

Paper.propTypes = {
  eventId: PropTypes.number.isRequired,
  contributionId: PropTypes.number.isRequired,
};
