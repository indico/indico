// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import resetReviewsURL from 'indico-url:event_editing.api_undo_review';

import React, {useState} from 'react';
import {useSelector, useDispatch} from 'react-redux';
import PropTypes from 'prop-types';
import {Icon, Popup} from 'semantic-ui-react';
import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import * as selectors from './selectors';
import {resetReviews} from './actions';

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
          confId: eventId,
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
        content="Undo review"
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
        confirmText={Translate.string('Yes')}
        cancelText={Translate.string('No')}
        onClose={() => setIsOpen(false)}
        content={
          <div className="content">
            <Translate>Are you sure you want to reset the review?</Translate>
          </div>
        }
        requestFunc={resetRevisions}
        open={isOpen}
      />
    </>
  );
}

ResetReview.propTypes = {
  revisionId: PropTypes.number.isRequired,
};
