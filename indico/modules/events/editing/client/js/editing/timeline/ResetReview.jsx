// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {resetReviews} from './actions';
import {isTimelineOutdated} from './selectors';

export default function ResetReview({reviewURL}) {
  const [submitting, setSubmitting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const isOutdated = useSelector(isTimelineOutdated);
  const dispatch = useDispatch();

  const resetRevisions = async () => {
    setSubmitting(true);
    await dispatch(resetReviews(reviewURL));
    setSubmitting(false);
  };

  return (
    <>
      <Popup
        content={
          isOutdated
            ? Translate.string('This timeline is outdated. Please refresh the page.')
            : Translate.string('Undo review')
        }
        trigger={
          <Icon
            name="undo"
            disabled={submitting || isOutdated}
            onClick={() => setIsOpen(true)}
            color="grey"
            size="large"
            link
          />
        }
      />
      <RequestConfirm
        header={Translate.string('Undo review')}
        confirmText={Translate.string('Undo')}
        onClose={() => setIsOpen(false)}
        requestFunc={resetRevisions}
        open={isOpen}
        negative
      >
        <Translate>Are you sure you want to undo the review?</Translate>
      </RequestConfirm>
    </>
  );
}

ResetReview.propTypes = {
  reviewURL: PropTypes.string.isRequired,
};
