// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadFileURL from 'indico-url:event_registration.upload_registration_file';

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalSingleFileManager} from 'indico/react/components';

import {getUpdateMode} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function FileInput({htmlName, disabled, isRequired}) {
  const {eventId, regformId, registrationUuid, fileData} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const initialFileDetails = isUpdateMode ? fileData[htmlName] || null : null;

  const urlParams = {
    event_id: eventId,
    reg_form_id: regformId,
  };
  if (registrationUuid) {
    urlParams.token = registrationUuid;
  }

  return (
    <div styleName="file-field">
      <FinalSingleFileManager
        name={htmlName}
        disabled={disabled}
        required={isRequired}
        uploadURL={uploadFileURL(urlParams)}
        initialFileDetails={initialFileDetails}
      />
    </div>
  );
}

FileInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
};

FileInput.defaultProps = {
  disabled: false,
  isRequired: false,
};
