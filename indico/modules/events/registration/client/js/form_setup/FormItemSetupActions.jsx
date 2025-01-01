// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch} from 'react-redux';

import {RequestConfirmDelete} from 'indico/react/components';
import {Translate, Param} from 'indico/react/i18n';

import * as actions from './actions';
import ItemSettingsModal from './ItemSettingsModal';

export default function FormItemSetupActions({
  id,
  title,
  fieldIsRequired,
  fieldIsPersonalData,
  isEnabled,
}) {
  const dispatch = useDispatch();
  const [settingsModalActive, setSettingsModalActive] = useState(false);
  const [confirmDeleteActive, setConfirmDeleteActive] = useState(false);

  const handleEnableClick = () => {
    dispatch(actions.enableItem(id));
  };

  const handleDisableClick = () => {
    dispatch(actions.disableItem(id));
  };

  const handleRemoveClick = () => {
    setConfirmDeleteActive(true);
  };

  const handleConfigureClick = () => {
    setSettingsModalActive(true);
  };

  return (
    <>
      {!fieldIsPersonalData && (
        <a
          className="icon-remove hide-if-locked"
          title={Translate.string('Remove field')}
          onClick={handleRemoveClick}
        />
      )}
      {!isEnabled && (
        <a
          className="icon-checkmark hide-if-locked"
          title={Translate.string('Enable field')}
          onClick={handleEnableClick}
        />
      )}
      {!fieldIsRequired && isEnabled && (
        <a
          className="icon-disable hide-if-locked"
          title={Translate.string('Disable field')}
          onClick={handleDisableClick}
        />
      )}
      <a
        className="icon-settings hide-if-locked"
        title={Translate.string('Configure field')}
        onClick={handleConfigureClick}
      />
      {settingsModalActive && (
        <ItemSettingsModal id={id} onClose={() => setSettingsModalActive(false)} />
      )}
      <RequestConfirmDelete
        requestFunc={() => dispatch(actions.removeItem(id))}
        onClose={() => setConfirmDeleteActive(false)}
        open={confirmDeleteActive}
        persistent
      >
        <Translate>
          Are you sure you want to delete the field "
          <Param name="field" value={title} wrapper={<strong />} />
          "?
        </Translate>
      </RequestConfirmDelete>
    </>
  );
}

FormItemSetupActions.propTypes = {
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  fieldIsRequired: PropTypes.bool.isRequired,
  fieldIsPersonalData: PropTypes.bool.isRequired,
  isEnabled: PropTypes.bool.isRequired,
};
