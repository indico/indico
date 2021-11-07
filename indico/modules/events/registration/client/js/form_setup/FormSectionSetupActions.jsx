// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useDispatch} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';

export default function FormSectionSetupActions({id, isPersonalData}) {
  const dispatch = useDispatch();

  const handleDisableClick = () => {
    dispatch(actions.disableSection(id));
  };

  return (
    <>
      {!isPersonalData && (
        <a
          className="icon-disable hide-if-locked"
          title={Translate.string('Disable section')}
          onClick={handleDisableClick}
        />
      )}
      <a className="icon-settings hide-if-locked" title={Translate.string('Configure section')} />
    </>
  );
}

FormSectionSetupActions.propTypes = {
  id: PropTypes.number.isRequired,
  isPersonalData: PropTypes.bool.isRequired,
};
