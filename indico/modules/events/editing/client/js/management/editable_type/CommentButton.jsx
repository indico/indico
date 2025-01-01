// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalCheckbox, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

export default function CommentButton({onSubmit, loading, disabled}) {
  const [modalOpen, setModalOpen] = useState(false);

  const handleSubmit = async (formData, form) => {
    const rv = await onSubmit(formData, form);
    if (!rv) {
      setModalOpen(false);
    }
  };

  return (
    <>
      <Button
        content={Translate.string('Comment', 'Leave a comment (verb)')}
        loading={loading}
        disabled={disabled}
        onClick={() => setModalOpen(true)}
      />
      {modalOpen && <CommentModal onSubmit={handleSubmit} onClose={() => setModalOpen(false)} />}
    </>
  );
}

CommentButton.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  disabled: PropTypes.bool.isRequired,
};

function CommentModal({onSubmit, onClose}) {
  return (
    <FinalModalForm
      id="comment-form"
      header={Translate.string('Comment', 'Comment modal title')}
      onSubmit={onSubmit}
      onClose={onClose}
    >
      <FinalTextArea
        name="text"
        placeholder={Translate.string('Leave a comment...')}
        hideValidationError
        autoFocus
        required
      />
      <FinalCheckbox
        label={Translate.string('Restrict visibility of this comment to other editors only')}
        name="internal"
        showAsToggle
      />
    </FinalModalForm>
  );
}

CommentModal.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};
