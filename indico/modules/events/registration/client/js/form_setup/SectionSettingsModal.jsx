// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector, useDispatch} from 'react-redux';

import {FinalInput, FinalTextArea, FinalCheckbox} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate, Param} from 'indico/react/i18n';

import * as actions from './actions';
import {getSectionById} from './selectors';

import '../../styles/regform.module.scss';

export default function SectionSettingsModal({id, onClose}) {
  const dispatch = useDispatch();
  const editing = id !== null;
  const {title, description, isPersonalData, isManagerOnly} = useSelector(state =>
    editing ? getSectionById(state, id) : {}
  );

  const handleSubmit = async formData => {
    const action = editing ? actions.updateSection(id, formData) : actions.createSection(formData);
    const rv = await dispatch(action);
    if (rv.error) {
      return rv.error;
    }
    onClose();
  };

  return (
    <FinalModalForm
      id="regform-section-settings"
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={editing ? {title, description, is_manager_only: isManagerOnly} : null}
      header={
        editing ? (
          <Translate>
            Configure section "<Param name="section" value={title} />"
          </Translate>
        ) : (
          <Translate>Add new section</Translate>
        )
      }
    >
      <FinalInput name="title" label={Translate.string('Title')} required autoFocus />
      <FinalTextArea
        name="description"
        label={Translate.string('Description')}
        description={<Translate>You may use Markdown for formatting.</Translate>}
      />
      <FinalCheckbox
        disabled={isPersonalData}
        name="is_manager_only"
        label={Translate.string('Manager-only')}
        description={<Translate>Whether the section is only visible for managers.</Translate>}
      />
    </FinalModalForm>
  );
}

SectionSettingsModal.propTypes = {
  id: PropTypes.number,
  onClose: PropTypes.func.isRequired,
};

SectionSettingsModal.defaultProps = {
  id: null,
};
