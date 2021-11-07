// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate} from 'indico/react/i18n';

import FormItem from './FormItem';

import '../../styles/regform.module.scss';

export default function FormSection({
  title,
  description,
  isManagerOnly,
  items,
  sortHandle,
  ItemComponent,
  itemProps,
  setupMode,
  setupActions,
}) {
  const enabledFields = items.filter(item => item.isEnabled);
  const disabledFields = setupMode ? items.filter(item => !item.isEnabled) : [];

  return (
    <div className={`regform-section ${isManagerOnly ? 'manager-only' : ''}`}>
      {sortHandle}
      <div className="i-box-header">
        <div className="i-box-title">{title}</div>
        <div className="i-box-description">{description}</div>
        {setupActions && (
          <div className="i-box-buttons" styleName="section-actions">
            {setupActions}
          </div>
        )}
      </div>
      <div className="i-box-content">
        {enabledFields.map((item, index) => (
          <ItemComponent
            key={item.id}
            index={index}
            setupMode={setupMode}
            {...itemProps}
            {...item}
          />
        ))}
        {disabledFields.length > 0 && (
          <>
            <div className="titled-rule section-field-divisor">
              <Translate>Disabled fields</Translate>{' '}
              <i
                className="info-helper"
                title={Translate.string("These fields won't be displayed to registrants")}
              />
            </div>
            {disabledFields.map((item, index) => (
              <ItemComponent
                key={item.id}
                index={index}
                setupMode={setupMode}
                {...itemProps}
                {...item}
              />
            ))}
          </>
        )}
      </div>
    </div>
  );
}

FormSection.propTypes = {
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  enabled: PropTypes.bool.isRequired,
  position: PropTypes.number.isRequired,
  /** Whether the section is a special "manager only" section */
  isManagerOnly: PropTypes.bool.isRequired,
  /** Whether the section is the special "personal data" section */
  isPersonalData: PropTypes.bool.isRequired,
  /** The form items in the section */
  items: PropTypes.arrayOf(PropTypes.shape(FormItem.propTypes)).isRequired,
  /** The handle to sort the section during setup */
  sortHandle: PropTypes.node,
  /** The react component to render individual form items */
  ItemComponent: PropTypes.elementType,
  /** Additional props passed to each item component */
  itemProps: PropTypes.object,
  /** Whether the registration form is currently being set up */
  setupMode: PropTypes.bool,
  /** Actions available during form setup */
  setupActions: PropTypes.node,
};

FormSection.defaultProps = {
  setupMode: false,
  setupActions: null,
  sortHandle: null,
  ItemComponent: FormItem,
  itemProps: {},
};
