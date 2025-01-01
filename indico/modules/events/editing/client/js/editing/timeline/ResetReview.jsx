// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch} from 'react-redux';
import {Icon, Popup} from 'semantic-ui-react';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import {resetReviews} from './actions';

export default function ResetReview({reviewURL}) {
  const [submitting, setSubmitting] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const dispatch = useDispatch();

  const resetRevisions = async () => {
    setSubmitting(true);
    await dispatch(resetReviews(reviewURL));
    setSubmitting(false);
  };

  return (
    <>
      <Popup
        content={Translate.string('Undo review')}
        trigger={
          <Icon
            name="undo"
            disabled={submitting}
            onClick={() => setIsOpen(true)}
            color="grey"
            size="large"
            link
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
  reviewURL: PropTypes.string.isRequired,
};
