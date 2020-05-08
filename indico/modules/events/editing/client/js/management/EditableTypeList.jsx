// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import enabledEditableTypesURL from 'indico-url:event_editing.api_enabled_editable_types';
import manageEditableTypeURL from 'indico-url:event_editing.manage_editable_type';
import manageEditableTypeListURL from 'indico-url:event_editing.manage_editable_type_list';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Button, Checkbox, Form, Loader, Popup} from 'semantic-ui-react';
import {Link} from 'react-router-dom';
import {Form as FinalForm} from 'react-final-form';
import {Translate} from 'indico/react/i18n';
import {useIndicoAxios} from 'indico/react/hooks';
import {FinalCheckbox, FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {indicoAxios} from 'indico/utils/axios';
import {editableTypeOrder, EditableTypeTitles} from '../models';

import './EditableTypeList.module.scss';

export default function EditableTypeList({eventId}) {
  const [editMode, setEditMode] = useState(false);
  const {
    data: enabledEditableTypes,
    loading: isLoadingEnabledEditableTypes,
    reFetch,
  } = useIndicoAxios({
    url: enabledEditableTypesURL({confId: eventId}),
    camelize: true,
    trigger: eventId,
  });

  if (isLoadingEnabledEditableTypes) {
    return <Loader inline="centered" active />;
  } else if (!enabledEditableTypes) {
    return null;
  }

  const handleSubmit = async formData => {
    const url = enabledEditableTypesURL({confId: eventId});
    const enabledTypes = Object.keys(formData).filter(name => formData[name]);
    try {
      await indicoAxios.post(url, {editable_types: enabledTypes});
    } catch (e) {
      return handleSubmitError(e);
    }
    reFetch();
    setEditMode(false);
  };

  const renderEditMode = () => {
    return (
      <FinalForm
        onSubmit={handleSubmit}
        subscription={{submitting: true}}
        initialValues={Object.assign(
          ...editableTypeOrder.map(type => ({[type]: enabledEditableTypes.includes(type)}))
        )}
      >
        {fprops => (
          <>
            <Form id="editable-type-form" onSubmit={fprops.handleSubmit}>
              <div className="action-box">
                {editableTypeOrder.map(type => (
                  <div key={type} className="section">
                    <span className="icon icon-file" />
                    <div className="text">
                      <div className="label">{EditableTypeTitles[type]}</div>
                    </div>
                    <div className="toolbar" styleName="switch-toolbar">
                      <FinalCheckbox name={type} toggle label="" styleName="type-switch" />
                    </div>
                  </div>
                ))}
              </div>
            </Form>
            <div className="toolbar f-j-end">
              <Button onClick={() => setEditMode(false)} disabled={fprops.submitting}>
                <Translate>Cancel</Translate>
              </Button>
              <FinalSubmitButton form="editable-type-form" label={Translate.string('Save')} />
            </div>
          </>
        )}
      </FinalForm>
    );
  };

  const renderListMode = () => {
    return enabledEditableTypes.length === 0 ? (
      <span styleName="disabled">
        <Translate>
          No editable types enabled yet. Click the toggle to enable any editable types.
        </Translate>
      </span>
    ) : (
      <div className="action-box">
        {enabledEditableTypes.map(type => (
          <div key={type} className="section">
            <span className="icon icon-file" />
            <div className="text">
              <div className="label">{EditableTypeTitles[type]}</div>
            </div>
            <div className="toolbar">
              <Link
                className="i-button icon-list"
                to={manageEditableTypeListURL({confId: eventId, type})}
              >
                <Translate>List</Translate>
              </Link>
              <Link
                className="i-button icon-settings"
                to={manageEditableTypeURL({confId: eventId, type})}
              >
                <Translate>Manage</Translate>
              </Link>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div styleName="editable-list">
      <div styleName="header">
        <h3>
          <Translate>List of editable types</Translate>
        </h3>
        <Popup
          content={Translate.string('Toggle editable types')}
          trigger={<Checkbox checked={editMode} toggle onClick={() => setEditMode(!editMode)} />}
        />
      </div>
      {editMode ? renderEditMode() : renderListMode()}
    </div>
  );
}

EditableTypeList.propTypes = {
  eventId: PropTypes.number.isRequired,
};
