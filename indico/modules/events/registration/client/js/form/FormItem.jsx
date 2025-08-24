// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect} from 'react';
import {useForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form, Icon, Popup} from 'semantic-ui-react';

import {PluralTranslate, Translate} from 'indico/react/i18n';
import {Markdown, toClasses} from 'indico/react/util';
import {renderPluginComponents} from 'indico/utils/plugins';

import {getManagement, getUpdateMode, isPaidItemLocked} from '../form_submission/selectors';

import {getFieldRegistry} from './fields/registry';
import {isItemHidden} from './selectors';

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

function PurgedItemLocked({isUpdateMode}) {
  const purgedMsg = <Translate>This field is locked due to an expired retention period.</Translate>;
  const msg = !isUpdateMode ? (
    purgedMsg
  ) : (
    <>
      {purgedMsg} <Translate>The associated registration data has been deleted.</Translate>
    </>
  );
  return <Popup trigger={<Icon name="lock" />}>{msg}</Popup>;
}

PurgedItemLocked.propTypes = {
  isUpdateMode: PropTypes.bool.isRequired,
};

function ItemLocked({reason}) {
  return <Popup trigger={<Icon name="lock" />}>{reason}</Popup>;
}

ItemLocked.propTypes = {
  reason: PropTypes.string.isRequired,
};

function ItemConditional({reason}) {
  return <Popup trigger={<Icon name="code branch" styleName="conditional" />}>{reason}</Popup>;
}

ItemConditional.propTypes = {
  reason: PropTypes.string.isRequired,
};

function renderAsFieldset(fieldOptions, meta) {
  if (typeof meta.renderAsFieldset === 'function') {
    return meta.renderAsFieldset(fieldOptions);
  }
  return meta.renderAsFieldset;
}

export default function FormItem({
  id,
  title,
  description,
  retentionPeriod,
  inputType,
  isEnabled,
  isRequired,
  isPurged,
  lockedReason,
  sortHandle,
  setupMode,
  setupActions,
  showIfFieldId,
  htmlName,
  defaultValue,
  ...rest
}) {
  // TODO move outside like with setupActions etc?
  const paidItemLocked = useSelector(state => isPaidItemLocked(state, id));
  const isManagement = useSelector(getManagement);
  const isUpdateMode = useSelector(getUpdateMode);
  const form = useForm();

  const fieldRegistry = getFieldRegistry();
  const meta = fieldRegistry[inputType] || {};
  const InputComponent = meta.inputComponent;
  const inputProps = {title, description, isEnabled, fieldId: id, ...rest};
  const showPurged = !setupMode && isPurged;
  const disabled = !isEnabled || showPurged || !!lockedReason || (paidItemLocked && !isManagement);

  const fieldOptions = {
    id,
    title,
    description,
    retentionPeriod,
    inputType,
    isEnabled,
    isRequired,
    isPurged,
    lockedReason,
    sortHandle,
    setupMode,
    setupActions,
    showIfFieldId,
    ...rest,
    meta,
  };
  let retentionPeriodIcon = null;
  if (setupMode && retentionPeriod) {
    retentionPeriodIcon = (
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
    );
  }

  const showAsRequired = meta.alwaysRequired || isRequired;
  const inputRequired = !isManagement && showAsRequired;
  const htmlId = `input-${inputProps.fieldId}`;

  const show = useSelector(state => !isItemHidden(state, id));

  const fieldControls =
    InputComponent && !meta.customFormItem ? (
      <>
        {retentionPeriodIcon}
        <InputComponent
          isRequired={inputRequired}
          disabled={disabled}
          isPurged={showPurged}
          htmlId={htmlId}
          htmlName={htmlName}
          {...inputProps}
        />
      </>
    ) : null;

  useEffect(() => {
    if (!show && !setupMode && inputType !== 'label') {
      form.change(htmlName, defaultValue);
    }
  }, [show, setupMode, form, htmlName, inputType, defaultValue]);

  if (!show && !setupMode) {
    return null;
  }

  return (
    <div
      data-html-name={htmlName}
      styleName={`form-item ${toClasses({
        disabled: !isEnabled || paidItemLocked,
        'purged-disabled': showPurged,
        'paid-disabled': !showPurged && paidItemLocked,
        editable: setupMode,
        'management-hidden': !show,
      })}`}
    >
      {sortHandle}
      <div styleName="content">
        {InputComponent ? (
          meta.customFormItem ? (
            <InputComponent
              showAsRequired={showAsRequired}
              isRequired={inputRequired}
              disabled={disabled}
              isPurged={showPurged}
              retentionPeriodIcon={retentionPeriodIcon}
              htmlId={htmlId}
              htmlName={htmlName}
              {...inputProps}
            />
          ) : (
            <Form.Field required={showAsRequired} styleName="field">
              {renderAsFieldset(fieldOptions, meta) ? (
                <fieldset id={htmlId} disabled={disabled}>
                  <legend>{title}</legend>
                  {fieldControls}
                </fieldset>
              ) : (
                <>
                  <label
                    htmlFor={htmlId}
                    style={{opacity: disabled ? 0.8 : 1, display: 'inline-block'}}
                  >
                    {title}
                  </label>
                  {fieldControls}
                </>
              )}
            </Form.Field>
          )
        ) : (
          `Unknown input type: ${inputType}`
        )}
        {description && (
          <div styleName="description">
            <Markdown targetBlank>{description}</Markdown>
          </div>
        )}
        {renderPluginComponents(`regform-${inputType}-field-item`, {htmlName, ...inputProps})}
      </div>
      <div styleName="actions">
        {setupActions}
        {lockedReason && <ItemLocked reason={lockedReason} />}
        {!!showIfFieldId && setupMode && (
          <ItemConditional reason={Translate.string('This field is conditionally shown')} />
        )}
        {!lockedReason && showPurged && <PurgedItemLocked isUpdateMode={isUpdateMode} />}
        {!lockedReason && !showPurged && paidItemLocked && (
          <PaidItemLocked management={isManagement} />
        )}
      </div>
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
  /** Whether the field's registration data have been deleted due to an expired retention period */
  isPurged: PropTypes.bool.isRequired,
  /** If the field is locked for some external reason, the reason for it */
  lockedReason: PropTypes.string,
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
  /** The ID of the field to use as condition for display */
  showIfFieldId: PropTypes.number,
  /** The default value for a given field **/
  defaultValue: PropTypes.any,
  // ... and various other field-specific keys (billing, limited-places, other config)
};

FormItem.defaultProps = {
  fieldIsPersonalData: false,
  fieldIsRequired: false,
  isRequired: false,
  lockedReason: '',
  retentionPeriod: null,
  htmlName: null,
  sortHandle: null,
  setupMode: false,
  setupActions: null,
  showIfFieldId: null,
  defaultValue: null,
};
