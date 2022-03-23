// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Form, Icon, Popup} from 'semantic-ui-react';

import {PluralTranslate, Translate} from 'indico/react/i18n';
import {Markdown, toClasses} from 'indico/react/util';

import {getManagement, isPaidItemLocked} from '../form_submission/selectors';

import {getFieldRegistry} from './fields/registry';

import '../../styles/regform.module.scss';

function PaidItemLocked({management}) {
  const lockedMsg = (
    <Translate>This field is locked since changing it could trigger a price change.</Translate>
  );
  const msg = !management ? (
    lockedMsg
  ) : (
    <>
      {lockedMsg} <Translate>As a manager you can modify it nonetheless.</Translate>
    </>
  );

  return <Popup trigger={<Icon name={management ? 'lock open' : 'lock'} />}>{msg}</Popup>;
}

PaidItemLocked.propTypes = {
  management: PropTypes.bool.isRequired,
};

export default function FormItem({
  title,
  description,
  retentionPeriod,
  inputType,
  isEnabled,
  isRequired,
  sortHandle,
  setupMode,
  setupActions,
  ...rest
}) {
  // TODO move outside like with setupActions etc?
  const paidItemLocked = useSelector(state => isPaidItemLocked(state, rest.id));
  const isManagement = useSelector(getManagement);

  const fieldRegistry = getFieldRegistry();
  const meta = fieldRegistry[inputType] || {};
  const InputComponent = meta.inputComponent;
  const inputProps = {title, description, isRequired, isEnabled, ...rest};
  const disabled = !isEnabled || (paidItemLocked && !isManagement);
  return (
    <div
      styleName={`form-item ${toClasses({
        'disabled': !isEnabled || paidItemLocked,
        'paid-disabled': paidItemLocked,
        'editable': setupMode,
      })}`}
    >
      {sortHandle}
      <div styleName="content">
        {InputComponent ? (
          meta.customFormItem ? (
            <InputComponent
              isRequired={isRequired || meta.alwaysRequired}
              disabled={disabled}
              {...inputProps}
            />
          ) : (
            <Form.Field required={isRequired || meta.alwaysRequired} styleName="field">
              <label style={{opacity: disabled ? 0.8 : 1, display: 'inline-block'}}>{title}</label>
              {setupMode && !!retentionPeriod && (
                <Icon
                  name="clock outline"
                  color="red"
                  style={{marginLeft: '3px'}}
                  title={PluralTranslate.string(
                    'Field data will be purged {retentionPeriod} week after the event ended.',
                    'Field data will be purged {retentionPeriod} weeks after the event ended.',
                    retentionPeriod,
                    {retentionPeriod}
                  )}
                />
              )}
              <InputComponent
                isRequired={isRequired || meta.alwaysRequired}
                disabled={disabled}
                {...inputProps}
              />
            </Form.Field>
          )
        ) : (
          `Unknown input type: ${inputType}`
        )}
        {description && (
          <div styleName="description">
            <Markdown>{description}</Markdown>
          </div>
        )}
      </div>
      {setupActions && <div styleName="actions">{setupActions}</div>}
      {paidItemLocked && <PaidItemLocked management={isManagement} />}
    </div>
  );
}

FormItem.propTypes = {
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  isEnabled: PropTypes.bool.isRequired,
  position: PropTypes.number.isRequired,
  /** Whether the field is required during registration */
  isRequired: PropTypes.bool,
  /** The retention period of the field's data in weeks */
  retentionPeriod: PropTypes.number,
  /** Whether the field is a special "personal data" field */
  fieldIsPersonalData: PropTypes.bool,
  /** Whether the field cannot be disabled */
  fieldIsRequired: PropTypes.bool,
  /** The HTML input name of the field (empty in case of static text) */
  htmlName: PropTypes.string,
  /** The widget type of the field */
  inputType: PropTypes.string.isRequired,
  /** The handle to sort the section during setup */
  sortHandle: PropTypes.node,
  /** Whether the field is being shown during form setup */
  setupMode: PropTypes.bool,
  /** Actions available during form setup */
  setupActions: PropTypes.node,
  // ... and various other field-specific keys (billing, limited-places, other config)
};

FormItem.defaultProps = {
  fieldIsPersonalData: false,
  fieldIsRequired: false,
  isRequired: false,
  retentionPeriod: null,
  htmlName: null,
  sortHandle: null,
  setupMode: false,
  setupActions: null,
};
