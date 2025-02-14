// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field, useFormState} from 'react-final-form';
import {OnChange} from 'react-final-form-listeners';
import {Button, Dropdown, Form, Input, Popup, Radio, TextArea, Icon} from 'semantic-ui-react';

import Checkbox from 'indico/react/components/Checkbox';

import formatters from './formatters';
import parsers from './parsers';
import validators from './validators';

import './fields.module.scss';

const identity = v => v;
export const unsortedArraysEqual = (a, b) => _.isEqual((a || []).sort(), (b || []).sort());

export function FormFieldAdapter({
  input: {name, value, ...input},
  id,
  autoId,
  label,
  placeholder,
  required,
  children,
  disabled,
  componentLabel,
  defaultValue,
  fieldProps,
  hideValidationError,
  hideErrorWhileActive,
  loaderWhileValidating,
  undefinedValue,
  meta: {touched, error, submitError, submitting, dirty, dirtySinceLastSubmit, active, validating},
  as: Component,
  getValue,
  ...props
}) {
  // we show errors if:
  // - the field was touched (focused+unfocused)
  //   ...and failed local validation
  //   ...and does not have the initial value
  // - there was an error during submission
  //   ...and the field has not been modified since the failed submission
  let errorMessage = null;
  let hasValidationError = false;
  if (error && hideValidationError === 'never') {
    errorMessage = error;
  } else if (touched && error && (dirty || required)) {
    if (!hideValidationError) {
      errorMessage = error;
    } else if (hideValidationError === 'message') {
      // if we only hide the message, we still want to apply the error styling
      hasValidationError = true;
    }
  } else if (submitError && !dirtySinceLastSubmit && !submitting) {
    errorMessage = submitError;
  }

  const showErrorPopup = !!errorMessage && (!hideErrorWhileActive || !active);

  const handleChange = (...args) => {
    if (getValue) {
      input.onChange(getValue(...args));
    } else {
      input.onChange(...args);
    }
  };

  if (input.checked === undefined) {
    // some components such as the react-dates picker log an error if an
    // unexpected prop is passed, even if it's undefined...
    delete input.checked;
  }

  if (loaderWhileValidating) {
    input.loading = validating;
  }

  const labelProps = {};
  if (autoId) {
    input.id = id || `finalfield-${name}`;
    labelProps.htmlFor = input.id;
  } else if (id) {
    input.id = id;
  }

  const field = (
    <Form.Field
      required={required}
      disabled={disabled || submitting}
      error={!!errorMessage || hasValidationError}
      defaultValue={defaultValue}
      {...fieldProps}
    >
      {label && <label {...labelProps}>{label}</label>}
      <Component
        name={name}
        {...input}
        value={value === undefined ? undefinedValue : value}
        {...props}
        onChange={handleChange}
        label={componentLabel}
        placeholder={placeholder}
        required={required}
        disabled={disabled || submitting}
      />
      {children}
    </Form.Field>
  );

  return (
    // The open prop is only false when there is no error. If there is an error,
    // we will let the `trigger` control it, as opposed to setting it true.
    <Popup
      trigger={field}
      position="left center"
      open={showErrorPopup && undefined}
      on={['hover', 'focus']}
    >
      <div styleName="field-error">{errorMessage}</div>
    </Popup>
  );
}

FormFieldAdapter.propTypes = {
  id: PropTypes.string,
  autoId: PropTypes.bool,
  disabled: PropTypes.bool,
  input: PropTypes.object.isRequired,
  required: PropTypes.bool,
  hideValidationError: PropTypes.oneOf([true, false, 'message', 'never']),
  hideErrorWhileActive: PropTypes.bool,
  undefinedValue: PropTypes.any,
  label: PropTypes.string,
  componentLabel: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  placeholder: PropTypes.string,
  meta: PropTypes.object.isRequired,
  as: PropTypes.elementType.isRequired,
  children: PropTypes.node,
  defaultValue: PropTypes.any,
  loaderWhileValidating: PropTypes.bool,
  fieldProps: PropTypes.object,
  getValue: PropTypes.func,
};

FormFieldAdapter.defaultProps = {
  id: undefined,
  autoId: true,
  disabled: false,
  required: false,
  hideValidationError: false,
  hideErrorWhileActive: false,
  undefinedValue: '',
  placeholder: undefined,
  label: null,
  componentLabel: null,
  children: null,
  defaultValue: null,
  loaderWhileValidating: false,
  fieldProps: {},
  getValue: null,
};

export function RadioAdapter(props) {
  const {
    input,
    // eslint-disable-next-line react/prop-types
    type, // unused, just don't pass it along with the ...rest
    ...rest
  } = props;
  return (
    <FormFieldAdapter
      input={input}
      {...rest}
      as={Radio}
      getValue={(__, {value}) => value}
      autoId={false}
    />
  );
}

RadioAdapter.propTypes = {
  input: PropTypes.object.isRequired,
};

function CheckboxAdapter(props) {
  const {
    input: {value, ...input},
    // eslint-disable-next-line react/prop-types
    type, // unused, just don't pass it along with the ...rest
    ...rest
  } = props;
  return (
    <FormFieldAdapter
      input={input}
      {...rest}
      as={Checkbox}
      getValue={(__, {checked}) => {
        // https://github.com/final-form/react-final-form/issues/543#issuecomment-504986394
        // we provide a fake event object which will be handled by the `input.onChange()`
        // handler inside by react-final-form
        return {target: {type: 'checkbox', value, checked}};
      }}
    />
  );
}

CheckboxAdapter.propTypes = {
  input: PropTypes.object.isRequired,
};

function DropdownAdapter(props) {
  const {input, required, clearable, isMultiple, width, action, ...rest} = props;
  const fieldProps = width !== null ? {width} : {};

  return (
    <FormFieldAdapter
      input={input}
      {...rest}
      required={required}
      as={action ? DropdownAction : Dropdown}
      clearable={clearable === undefined ? !required && !isMultiple : clearable}
      multiple={isMultiple}
      undefinedValue={isMultiple ? [] : null}
      selectOnBlur={false}
      selectOnNavigation={false}
      fieldProps={fieldProps}
      getValue={(__, {value}) => value}
      action={action}
    />
  );
}

DropdownAdapter.propTypes = {
  input: PropTypes.object.isRequired,
  required: PropTypes.bool,
  clearable: PropTypes.bool,
  isMultiple: PropTypes.bool,
  width: PropTypes.number,
  action: PropTypes.object,
};

DropdownAdapter.defaultProps = {
  required: false,
  clearable: undefined,
  isMultiple: false,
  width: null,
  action: null,
};

function ComboDropdownAdapter(props) {
  const {
    input,
    required,
    clearable,
    width,
    action,
    options,
    renderCustomOptionContent,
    includeMeta,
    ...rest
  } = props;
  const fieldProps = width !== null ? {width} : {};

  let fullOptions = options;
  if (typeof input.value === 'string' && input.value) {
    fullOptions = [
      {
        key: 'custom',
        value: input.value,
        text: input.value,
        content: renderCustomOptionContent(input.value),
      },
      ...options,
    ];
  }

  return (
    <FormFieldAdapter
      input={input}
      {...rest}
      options={fullOptions}
      required={required}
      as={action ? DropdownAction : Dropdown}
      clearable={clearable === undefined ? !required : clearable}
      multiple={false}
      action={action}
      undefinedValue={null}
      selectOnBlur={false}
      selectOnNavigation={false}
      fieldProps={fieldProps}
      getValue={(__, {value}) => {
        if (typeof value === 'number') {
          const opt = options.find(x => x.value === value);
          const rv = {
            id: value,
            text: opt.text,
          };
          if (includeMeta) {
            rv.meta = opt.meta;
          }
          return rv;
        } else {
          const rv = {
            id: null,
            text: value,
          };
          if (includeMeta) {
            rv.meta = null;
          }
          return rv;
        }
      }}
      onAddItem={(e, {value}) => {
        input.onChange({
          id: null,
          text: value,
        });
      }}
    />
  );
}

ComboDropdownAdapter.propTypes = {
  input: PropTypes.object.isRequired,
  options: PropTypes.array.isRequired,
  required: PropTypes.bool,
  clearable: PropTypes.bool,
  width: PropTypes.number,
  action: PropTypes.object,
  renderCustomOptionContent: PropTypes.func,
  includeMeta: PropTypes.bool,
};

ComboDropdownAdapter.defaultProps = {
  required: false,
  clearable: undefined,
  width: null,
  action: null,
  renderCustomOptionContent: () => undefined,
  includeMeta: false,
};

/**
 * A wrapper for final-form's Field component that handles the markup
 * around the field.
 */
export function FinalField({name, adapter, component, description, required, onChange, ...rest}) {
  const extraProps = {};

  if (description) {
    extraProps.children = <p styleName="field-description">{description}</p>;
  }

  if (required) {
    if (required !== 'no-validator') {
      // unless we opted out, add the required validator. note that you may want to
      // opt out from this if you have custom validation logic that should run in all
      // cases even when the required field is empty
      extraProps.validate = validators.required;
    }
    extraProps.required = true;
  }

  if (extraProps.validate && rest.validate) {
    extraProps.validate = validators.chain(extraProps.validate, rest.validate);
    delete rest.validate;
  } else if (rest.validate === null || rest.validate === undefined) {
    // avoid overwriting default (required) validator e.g. when conditionally setting a validator
    // on a field (and using null/undefined in case no validator is needed)
    delete rest.validate;
  }

  return (
    <>
      <Field name={name} component={adapter} as={component} {...extraProps} {...rest} />
      {onChange && (
        <OnChange name={name}>
          {(value, prev) => {
            if (!_.isEqual(value, prev)) {
              onChange(value, prev);
            }
          }}
        </OnChange>
      )}
    </>
  );
}

FinalField.propTypes = {
  name: PropTypes.string.isRequired,
  adapter: PropTypes.elementType,
  component: PropTypes.elementType,
  description: PropTypes.node,
  required: PropTypes.oneOf([true, false, 'no-validator']),
  /** A function that is called with the new and old value whenever the value changes. */
  onChange: PropTypes.func,
};

FinalField.defaultProps = {
  adapter: FormFieldAdapter,
  component: undefined,
  description: null,
  required: false,
  onChange: null,
};

/**
 * Like `FinalField` but with extra features for ``<input>`` fields.
 */
export function FinalInput({name, label, type, nullIfEmpty, noAutoComplete, ...rest}) {
  const extraProps = {};

  if (type === 'number') {
    extraProps.parse = parsers.number;
  } else if (type === 'text' || type === 'email' || type === 'tel') {
    extraProps.format = formatters.trim;
    extraProps.formatOnBlur = true;
    extraProps.parse = nullIfEmpty ? parsers.nullIfEmpty : identity;
  }

  if (noAutoComplete) {
    extraProps.autoComplete = 'off';
  }

  return (
    <FinalField
      name={name}
      label={label}
      component={Input}
      loaderWhileValidating
      type={type}
      {...extraProps}
      {...rest}
    />
  );
}

FinalInput.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
  // XXX: just add new <input> types here as soon as you start using them,
  // but make sure to handle it properly above (like adding the trim formatter
  // for a field that lets users enter strings)
  type: PropTypes.oneOf(['text', 'email', 'number', 'tel', 'password']),
  nullIfEmpty: PropTypes.bool,
  noAutoComplete: PropTypes.bool,
};

FinalInput.defaultProps = {
  label: null,
  type: 'text',
  nullIfEmpty: false,
  noAutoComplete: false,
};

/**
 * Like `FinalField` but with extra features for ``<textarea>`` fields.
 */
export function FinalTextArea({name, label, nullIfEmpty, action, ...rest}) {
  return (
    <FinalField
      name={name}
      label={label}
      component={action ? TextAreaAction : TextArea}
      format={formatters.trim}
      formatOnBlur
      parse={nullIfEmpty ? parsers.nullIfEmpty : identity}
      action={action}
      {...rest}
    />
  );
}

FinalTextArea.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
  nullIfEmpty: PropTypes.bool,
  action: PropTypes.object,
};

FinalTextArea.defaultProps = {
  label: null,
  nullIfEmpty: false,
  action: null,
};

/**
 * Like `FinalField` but for a checkbox.
 */
export function FinalCheckbox({name, label, value, ...rest}) {
  const extraProps = {};
  if (value !== undefined) {
    extraProps.isEqual = unsortedArraysEqual;
  }
  return (
    <FinalField
      name={name}
      adapter={CheckboxAdapter}
      format={v => v}
      type="checkbox"
      componentLabel={label}
      value={value}
      {...extraProps}
      {...rest}
    />
  );
}

FinalCheckbox.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.node,
    PropTypes.exact({children: PropTypes.node.isRequired}),
  ]).isRequired,
  value: PropTypes.string,
};

FinalCheckbox.defaultProps = {
  value: undefined,
};

/**
 * Like `FinalField` but for a radio button.
 */
export function FinalRadio({name, label, ...rest}) {
  return (
    <FinalField name={name} adapter={RadioAdapter} type="radio" componentLabel={label} {...rest} />
  );
}

FinalRadio.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
};

/**
 * Like `FinalField` but for a dropdown.
 */
export function FinalDropdown({name, label, multiple, ...rest}) {
  const extraProps = {};
  if (multiple) {
    extraProps.isEqual = unsortedArraysEqual;
  }
  return (
    <FinalField
      name={name}
      adapter={DropdownAdapter}
      label={label}
      format={identity}
      parse={identity}
      search
      deburr
      // https://github.com/final-form/react-final-form/issues/544
      isMultiple={multiple}
      {...extraProps}
      {...rest}
    />
  );
}

FinalDropdown.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
  multiple: PropTypes.bool,
};

FinalDropdown.defaultProps = {
  label: null,
  multiple: false,
};

/**
 * Like `FinalField` but for a dropdown with support for adding a custom freetext item.
 */
export function FinalComboDropdown({name, label, ...rest}) {
  return (
    <FinalField
      name={name}
      adapter={ComboDropdownAdapter}
      label={label}
      format={x => (x.id === null ? x.text : x.id)}
      parse={identity}
      allowAdditions
      search
      selection
      {...rest}
    />
  );
}

FinalComboDropdown.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
};

FinalComboDropdown.defaultProps = {
  label: null,
};

/**
 * A submit button that will update according to the final-form state.
 */
export function FinalSubmitButton({
  label,
  form,
  disabledUntilChange,
  disabledIfInvalid,
  disabledAfterSubmit,
  activeSubmitButton,
  color,
  onClick,
  circular,
  size,
  icon,
  fluid,
  style,
  children,
  extraSubscription,
}) {
  const {
    validating,
    hasValidationErrors,
    pristine,
    submitting,
    submitError,
    submitSucceeded,
  } = useFormState({
    subscription: {
      validating: true,
      hasValidationErrors: true,
      pristine: true,
      submitting: true,
      submitError: true,
      submitSucceeded: true,
      ...extraSubscription,
    },
  });
  const disabled =
    validating ||
    (disabledIfInvalid && hasValidationErrors) ||
    (disabledUntilChange && pristine) ||
    (disabledAfterSubmit && submitSucceeded) ||
    submitting;
  return (
    <Form.Field disabled={disabled} style={style}>
      <Popup
        trigger={
          <Button
            type="submit"
            form={form}
            disabled={disabled}
            loading={submitting && activeSubmitButton}
            primary={color === null}
            content={label}
            color={color}
            onClick={onClick}
            circular={circular}
            size={size}
            icon={icon}
            fluid={fluid}
          />
        }
        position="bottom right"
        open={!!submitError}
      >
        <div styleName="field-error">{submitError}</div>
      </Popup>
      {children && children(disabled)}
    </Form.Field>
  );
}

FinalSubmitButton.propTypes = {
  label: PropTypes.string,
  form: PropTypes.string,
  disabledUntilChange: PropTypes.bool,
  disabledIfInvalid: PropTypes.bool,
  disabledAfterSubmit: PropTypes.bool,
  activeSubmitButton: PropTypes.bool,
  color: PropTypes.string,
  onClick: PropTypes.func,
  circular: PropTypes.bool,
  icon: PropTypes.string,
  fluid: PropTypes.bool,
  size: PropTypes.string,
  style: PropTypes.object,
  extraSubscription: PropTypes.object,
  children: PropTypes.func,
};

FinalSubmitButton.defaultProps = {
  label: null,
  form: null,
  disabledUntilChange: true,
  disabledIfInvalid: true,
  disabledAfterSubmit: false,
  activeSubmitButton: true,
  color: null,
  onClick: null,
  circular: false,
  icon: null,
  fluid: false,
  size: null,
  style: null,
  extraSubscription: {},
  children: null,
};

/**
 * TextArea but with an action button attached.
 * This is similar to the native SUI functionality which works only for inputs.
 */
function TextAreaAction({className, action, ...rest}) {
  const minHeight = 39; // The height of SUI's <Input />
  return (
    <div
      className={className}
      style={{
        display: 'flex',
      }}
    >
      <TextArea
        {...rest}
        style={{
          borderTopRightRadius: 0,
          borderBottomRightRadius: 0,
          minHeight,
        }}
      />
      <ActionButton action={action} />
    </div>
  );
}

TextAreaAction.propTypes = {
  className: PropTypes.string,
  action: PropTypes.object.isRequired,
};

TextAreaAction.defaultProps = {
  className: '',
};

/**
 * Dropdown but with an action button attached.
 * This is similar to the native SUI functionality which works only for inputs.
 */
function DropdownAction({className, action, readOnly, ...rest}) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
      }}
    >
      <Dropdown
        {...rest}
        disabled={readOnly}
        style={{
          borderTopRightRadius: 0,
          borderBottomRightRadius: 0,
        }}
      />
      <ActionButton action={action} />
    </div>
  );
}

DropdownAction.propTypes = {
  className: PropTypes.string,
  action: PropTypes.object.isRequired,
  readOnly: PropTypes.bool,
};

DropdownAction.defaultProps = {
  className: '',
  readOnly: false,
};

function ActionButton({action}) {
  // The height of SUI's input
  // This makes the height of the action button that same as
  // the SUI's native action button for <Input />
  const minHeight = 39;
  return (
    <Button
      type="button"
      icon
      toggle={action.toggle}
      active={action.active}
      disabled={action.disabled}
      className={action.className}
      title={action.title}
      style={{
        alignSelf: 'flex-start',
        borderTopLeftRadius: 0,
        borderBottomLeftRadius: 0,
        marginRight: 0,
        height: minHeight,
      }}
      onClick={action.onClick}
    >
      <Icon name={action.icon} />
    </Button>
  );
}

ActionButton.propTypes = {
  action: PropTypes.shape({
    type: PropTypes.oneOf(['button']).isRequired,
    active: PropTypes.bool,
    disabled: PropTypes.bool,
    icon: PropTypes.string.isRequired,
    toggle: PropTypes.bool,
    className: PropTypes.string,
    title: PropTypes.string,
    onClick: PropTypes.func,
  }).isRequired,
};

export function Fieldset({legend, children, active, compact}) {
  if (!active) {
    return children;
  }
  return (
    <fieldset styleName={`fieldset ${compact ? 'compact' : ''}`}>
      <legend>{legend}</legend>
      {children}
    </fieldset>
  );
}

Fieldset.propTypes = {
  legend: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  active: PropTypes.bool,
  compact: PropTypes.bool,
};

Fieldset.defaultProps = {
  active: true,
  compact: false,
};
