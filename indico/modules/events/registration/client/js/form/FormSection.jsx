// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {Markdown} from 'indico/react/util';

import FormItem from './FormItem';

import '../../styles/regform.module.scss';

export default function FormSection({
  title,
  description,
  isManagerOnly,
  items,
  sortHandle,
  itemComponent: ItemComponent,
  itemProps,
  setupMode,
  setupActions,
}) {
  const enabledFields = items.filter(item => item.isEnabled);
  const disabledFields = setupMode ? items.filter(item => !item.isEnabled) : [];

  const managerPopup = (
    <Popup
      content={Translate.string('This section is only visible to managers.')}
      trigger={<i className="icon-user-reading" style={{marginRight: 5}} />}
    />
  );

  return (
    <div className="regform-section" styleName={isManagerOnly ? 'manager-only' : null}>
      <div className="i-box-header">
        {sortHandle}
        <div styleName="header-wrapper">
          <h4 className="i-box-title">
            {isManagerOnly ? managerPopup : null}
            {title}
          </h4>
          <div className="i-box-description">
            <Markdown targetBlank>{description}</Markdown>
          </div>
        </div>
        {setupActions && (
          <div className="i-box-buttons" styleName="section-actions">
            {setupActions}
          </div>
        )}
      </div>
      <Form as="div" className="i-box-content">
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
      </Form>
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
  itemComponent: PropTypes.elementType,
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
  itemComponent: FormItem,
  itemProps: {},
};
