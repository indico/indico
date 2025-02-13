// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import managementPreviewURL from 'indico-url:event_registration.manage_registration_file';
import registrantPreviewURL from 'indico-url:event_registration.registration_picture';
import managementUploadURL from 'indico-url:event_registration.upload_picture_management';
import registrantUploadURL from 'indico-url:event_registration.upload_registration_picture';

import PropTypes from 'prop-types';
import React, {useMemo} from 'react';
import {useSelector} from 'react-redux';

import {FinalPictureManager} from 'indico/react/components';
import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getManagement} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function PictureInput({
  fieldId,
  htmlName,
  htmlId,
  disabled,
  isRequired,
  minPictureSize,
}) {
  const {eventId, regformId, registrationUuid, fileData} = useSelector(getStaticData);
  const initialPictureDetails = fileData ? fileData[htmlName] || null : null;
  const isManagement = useSelector(getManagement);
  const [invitationToken, formToken] = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return [params.get('invitation'), params.get('form_token')];
  }, []);

  const previewURL = isManagement ? managementPreviewURL : registrantPreviewURL;
  const uploadURL = isManagement ? managementUploadURL : registrantUploadURL;
  const uploadUrlParams = {
    event_id: eventId,
    reg_form_id: regformId,
    field_id: fieldId,
  };
  if (registrationUuid) {
    uploadUrlParams.token = registrationUuid;
  }
  if (invitationToken) {
    uploadUrlParams.invitation = invitationToken;
  }
  if (formToken) {
    uploadUrlParams.form_token = formToken;
  }
  const previewUrlParams = initialPictureDetails ? initialPictureDetails.locator : null;

  return (
    <div styleName="file-field" id={htmlId}>
      <FinalPictureManager
        name={htmlName}
        disabled={disabled}
        required={isRequired}
        uploadURL={uploadURL(uploadUrlParams)}
        previewURL={previewUrlParams ? previewURL(previewUrlParams) : ''}
        initialPictureDetails={initialPictureDetails}
        minPictureSize={minPictureSize}
      />
    </div>
  );
}

PictureInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  minPictureSize: PropTypes.number,
};

PictureInput.defaultProps = {
  disabled: false,
  isRequired: false,
  minPictureSize: null,
};

export function PictureSettings() {
  return (
    <FinalInput
      name="minPictureSize"
      type="number"
      label={Translate.string('Minimum picture size')}
      placeholder={Translate.string('Unlimited', 'Minimum size')}
      description={Translate.string(
        'Minimum picture size that can be uploaded in pixels. Leave empty for no min size validation.'
      )}
      step="1"
      min="25"
      max="1000"
      validate={v.optional(v.range(25, 1000))}
      fluid
    />
  );
}
