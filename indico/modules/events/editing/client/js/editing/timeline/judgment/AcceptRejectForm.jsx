// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getNonSystemTags} from '../selectors';

import FinalTagInput from './TagInput';

export default function AcceptRejectForm({action}) {
  const tagOptions = useSelector(getNonSystemTags);

  return (
    <>
      <FinalTextArea
        name="comment"
        placeholder={Translate.string('Leave a comment...')}
        hideValidationError
        autoFocus
        required={action === 'reject'}
        /* otherwise changing required doesn't work properly if the field has been touched */
        key={action}
      />
      <FinalTagInput name="tags" options={tagOptions} />
    </>
  );
}

AcceptRejectForm.propTypes = {
  action: PropTypes.oneOf(['accept', 'reject']).isRequired,
};
