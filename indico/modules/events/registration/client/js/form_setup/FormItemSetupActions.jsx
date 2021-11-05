// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

export default function FormItemSetupActions({fieldIsRequired, fieldIsPersonalData, isEnabled}) {
  return (
    <>
      {!fieldIsPersonalData && (
        <a className="icon-remove hide-if-locked" title={Translate.string('Remove field')} />
      )}
      {!isEnabled && (
        <a className="icon-checkmark hide-if-locked" title={Translate.string('Enable field')} />
      )}
      {!fieldIsRequired && isEnabled && (
        <a className="icon-disable hide-if-locked" title={Translate.string('Disable field')} />
      )}
      <a className="icon-settings hide-if-locked" title={Translate.string('Configure field')} />
    </>
  );
}

FormItemSetupActions.propTypes = {
  fieldIsRequired: PropTypes.bool.isRequired,
  fieldIsPersonalData: PropTypes.bool.isRequired,
  isEnabled: PropTypes.bool.isRequired,
};
