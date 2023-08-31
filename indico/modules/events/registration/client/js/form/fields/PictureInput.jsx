// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import previewURL from 'indico-url:event_registration.registration_picture';
import uploadURL from 'indico-url:event_registration.upload_registration_file';

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalPictureManager} from 'indico/react/components';
import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getUpdateMode} from '../../form_submission/selectors';
import {getStaticData} from '../selectors';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function PictureInput({htmlName, disabled, isRequired, minPictureSize}) {
  const {eventId, regformId, registrationUuid, fileData} = useSelector(getStaticData);
  const isUpdateMode = useSelector(getUpdateMode);
  const initialPictureDetails = isUpdateMode ? fileData[htmlName] || null : null;
  const uploadUrlParams = {
    event_id: eventId,
    reg_form_id: regformId,
  };
  if (registrationUuid) {
    uploadUrlParams.token = registrationUuid;
  }
  const previewUrlParams = initialPictureDetails ? initialPictureDetails.locator : null;

  return (
    <div styleName="file-field">
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
      placeholder={Translate.string('Unlimited')}
      description={Translate.string(
        'Minimum picture size that can be uploaded in pixels. Leave empty for no min size validation.'
      )}
      step="1"
      min="0"
      max="1200"
      validate={v.optional(v.min(0))}
      fluid
      format={val => val || ''}
      parse={val => +val || 0}
    />
  );
}
