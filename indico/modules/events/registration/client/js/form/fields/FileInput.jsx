// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import managementUploadURL from 'indico-url:event_registration.upload_file_management';
import participantUploadURL from 'indico-url:event_registration.upload_registration_file';

import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {useSelector} from 'react-redux';

import {FinalSingleFileManager} from 'indico/react/components';

import {getManagement, getUpdateMode} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function FileInput({fieldId, htmlId, htmlName, disabled, isRequired}) {
  const {eventId, regformId, registrationUuid, fileData} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const isManagement = useSelector(getManagement);
  const [invitationToken, formToken] = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return [params.get('invitation'), params.get('form_token')];
  }, []);

  const initialFileDetails = isUpdateMode ? fileData[htmlName] || null : null;

  const urlParams = {
    event_id: eventId,
    reg_form_id: regformId,
    field_id: fieldId,
  };
  if (registrationUuid) {
    urlParams.token = registrationUuid;
  }
  if (invitationToken) {
    urlParams.invitation = invitationToken;
  }
  if (formToken) {
    urlParams.form_token = formToken;
  }

  return (
    <div styleName="file-field" id={htmlId}>
      <FinalSingleFileManager
        name={htmlName}
        disabled={disabled}
        required={isRequired}
        uploadURL={isManagement ? managementUploadURL(urlParams) : participantUploadURL(urlParams)}
        initialFileDetails={initialFileDetails}
      />
    </div>
  );
}

FileInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
};

FileInput.defaultProps = {
  disabled: false,
  isRequired: false,
};
