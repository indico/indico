// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import resetReviewsURL from 'indico-url:event_editing.api_undo_review';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {resetReviews} from './actions';
import * as selectors from './selectors';

import './ResetReviews.module.scss';

export default function ResetReview({revisionId}) {
  const {eventId, contributionId, editableType} = useSelector(selectors.getStaticData);
  const allowed = useSelector(selectors.canPerformEditorActions);
  const [submitting, setSubmitting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch();

  if (!allowed) {
    return null;
  }

  const resetRevisions = async () => {
    setSubmitting(true);
    await dispatch(
      resetReviews(
        resetReviewsURL({
          event_id: eventId,
          contrib_id: contributionId,
          type: editableType,
          revision_id: revisionId,
        })
      )
    );
    setSubmitting(false);
  };

  return (
    <>
      <Popup
        content={Translate.string('Undo review')}
        trigger={
          <Icon
            styleName="reset-button"
            name="undo"
            disabled={submitting}
            onClick={() => setIsOpen(true)}
            color="grey"
            size="large"
          />
        }
      />
      <RequestConfirm
        header={Translate.string('Reset review')}
        confirmText={Translate.string('Reset')}
        onClose={() => setIsOpen(false)}
        requestFunc={resetRevisions}
        open={isOpen}
        negative
      >
        <Translate>Are you sure you want to reset the review?</Translate>
      </RequestConfirm>
    </>
  );
}

ResetReview.propTypes = {
  revisionId: PropTypes.number.isRequired,
};
