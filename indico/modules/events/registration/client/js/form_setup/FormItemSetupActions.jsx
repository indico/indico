// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';

import {RequestConfirm, RequestConfirmDelete} from 'indico/react/components';
import {Translate, Param} from 'indico/react/i18n';

import * as actions from './actions';
import ItemSettingsModal from './ItemSettingsModal';
import {isFieldConditionFor} from './selectors';

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
  const [confirmDisableActive, setConfirmDisableActive] = useState(false);
  const isCondition = useSelector(state => isFieldConditionFor(state, id));

  const handleEnableClick = () => {
    dispatch(actions.enableItem(id));
  };

  const handleDisableClick = () => {
    if (isCondition) {
      setConfirmDisableActive(true);
    } else {
      dispatch(actions.disableItem(id));
    }
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
          title={Translate.string('Delete field')}
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
      <RequestConfirm
        header={Translate.string('Are you sure you want to disable this field?')}
        confirmText={Translate.string('Disable field')}
        requestFunc={() => {
          setConfirmDisableActive(false);
          dispatch(actions.disableItem(id));
        }}
        onClose={() => setConfirmDisableActive(false)}
        open={confirmDisableActive}
        persistent
      >
        <Translate>
          Are you sure you want to disable the field "
          <Param name="field" value={title} wrapper={<strong />} />
          "?
        </Translate>
        <Translate as="p">
          This field is used as a condition for other fields. Disabling it will render those
          conditions ineffective.
        </Translate>
      </RequestConfirm>
      <RequestConfirmDelete
        requestFunc={() => {
          setConfirmDeleteActive(false);
          dispatch(actions.removeItem(id));
        }}
        onClose={() => setConfirmDeleteActive(false)}
        open={confirmDeleteActive}
        persistent
      >
        <Translate>
          Are you sure you want to delete the field "
          <Param name="field" value={title} wrapper={<strong />} />
          "?
        </Translate>
        {isCondition && (
          <Translate as="p">
            This field is used as a condition for other fields. Deleting it will permanently remove
            those conditional relationships. This action cannot be undone.
          </Translate>
        )}
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
