// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch} from 'react-redux';

import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import ItemSettingsModal from './ItemSettingsModal';
import ItemTypeDropdown from './ItemTypeDropdown';
import SectionSettingsModal from './SectionSettingsModal';

export default function FormSectionSetupActions({id, isPersonalData}) {
  const [settingsModalActive, setSettingsModalActive] = useState(false);
  const [fieldModalActive, setFieldModalActive] = useState(false);
  const [newItemType, setNewItemType] = useState(null);
  const dispatch = useDispatch();

  const handleDisableClick = () => {
    dispatch(actions.disableSection(id));
  };

  const handleConfigureClick = () => {
    setSettingsModalActive(true);
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
      <a
        className="icon-settings hide-if-locked"
        title={Translate.string('Configure section')}
        onClick={handleConfigureClick}
      />
      <ItemTypeDropdown
        inModal={false}
        onClick={value => {
          setNewItemType(value);
          setFieldModalActive(true);
        }}
      />
      {settingsModalActive && (
        <SectionSettingsModal id={id} onClose={() => setSettingsModalActive(false)} />
      )}
      {fieldModalActive && (
        <ItemSettingsModal
          sectionId={id}
          defaultNewItemType={newItemType}
          onClose={() => setFieldModalActive(false)}
        />
      )}
    </>
  );
}

FormSectionSetupActions.propTypes = {
  id: PropTypes.number.isRequired,
  isPersonalData: PropTypes.bool.isRequired,
};
