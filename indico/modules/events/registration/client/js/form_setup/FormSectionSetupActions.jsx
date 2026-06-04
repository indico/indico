// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import {RequestConfirm} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import ItemSettingsModal from './ItemSettingsModal';
import ItemTypeDropdown from './ItemTypeDropdown';
import SectionSettingsModal from './SectionSettingsModal';
import {sectionHasConditionalFields} from './selectors';

export default function FormSectionSetupActions({id, isPersonalData}) {
  const [settingsModalActive, setSettingsModalActive] = useState(false);
  const [fieldModalActive, setFieldModalActive] = useState(false);
  const [newItemType, setNewItemType] = useState(null);
  const [confirmDisableActive, setConfirmDisableActive] = useState(false);
  const dispatch = useDispatch();
  const hasConditionalFields = useSelector(state => sectionHasConditionalFields(state, id));

  const handleDisableClick = () => {
    if (hasConditionalFields) {
      setConfirmDisableActive(true);
    } else {
      dispatch(actions.disableSection(id));
    }
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
      <RequestConfirm
        header={Translate.string('Are you sure you want to disable this section?')}
        confirmText={Translate.string('Disable section')}
        onClose={() => setConfirmDisableActive(false)}
        requestFunc={() => {
          setConfirmDisableActive(false);
          dispatch(actions.disableSection(id));
        }}
        open={confirmDisableActive}
        persistent
      >
        <Translate>
          This section contains fields that are used as conditions for other fields. Those
          conditions will be inactive while this section is disabled, but may be restored when the
          section is re-enabled.
        </Translate>
      </RequestConfirm>
    </>
  );
}

FormSectionSetupActions.propTypes = {
  id: PropTypes.number.isRequired,
  isPersonalData: PropTypes.bool.isRequired,
};
