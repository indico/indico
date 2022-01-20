// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadFileURL from 'indico-url:event_registration.upload_registration_file';

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalSingleFileManager} from 'indico/react/components';

import {getStaticData} from '../../form_setup/selectors';

import '../../../styles/regform.module.scss';
import './FileInput.module.scss';

export default function FileInput({htmlName, disabled, isRequired}) {
  const {eventId, regformId} = useSelector(getStaticData);

  return (
    <FinalSingleFileManager
      name={htmlName}
      disabled={disabled}
      required={isRequired}
      uploadURL={uploadFileURL({event_id: eventId, reg_form_id: regformId})}
      hideValidationError
    />
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
