// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Button, Checkbox, Dropdown, Form, Input, Popup, Radio, TextArea} from 'semantic-ui-react';
import {Field, useFormState} from 'react-final-form';
import {OnChange} from 'react-final-form-listeners';

import formatters from './formatters';
import parsers from './parsers';
import validators from './validators';

import './fields.module.scss';

const identity = v => v;
export const unsortedArraysEqual = (a, b) => _.isEqual((a || []).sort(), (b || []).sort());

export function FormFieldAdapter({
  input: {value, ...input},
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
  if (touched && error && (dirty || required)) {
    if (!hideValidationError) {
      errorMessage = error;
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

  const field = (
    <Form.Field
      required={required}
      disabled={disabled || submitting}
      error={!!errorMessage}
      defaultValue={defaultValue}
      {...fieldProps}
    >
      {label && <label>{label}</label>}
      <Component
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
  disabled: PropTypes.bool,
  input: PropTypes.object.isRequired,
  required: PropTypes.bool,
  hideValidationError: PropTypes.bool,
  hideErrorWhileActive: PropTypes.bool,
  undefinedValue: PropTypes.any,
  label: PropTypes.string,
  componentLabel: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.exact({children: PropTypes.node}),
  ]),
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
  return <FormFieldAdapter input={input} {...rest} as={Radio} getValue={(__, {value}) => value} />;
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
  const {input, required, clearable, isMultiple, width, ...rest} = props;
  const fieldProps = width !== null ? {width} : {};

  return (
    <FormFieldAdapter
      input={input}
      {...rest}
      required={required}
      as={Dropdown}
      clearable={clearable === undefined ? !required && !isMultiple : clearable}
      multiple={isMultiple}
      undefinedValue={isMultiple ? [] : null}
      selectOnBlur={false}
      fieldProps={fieldProps}
      getValue={(__, {value}) => value}
    />
  );
}

DropdownAdapter.propTypes = {
  input: PropTypes.object.isRequired,
  required: PropTypes.bool,
  clearable: PropTypes.bool,
  isMultiple: PropTypes.bool,
  width: PropTypes.number,
};

DropdownAdapter.defaultProps = {
  required: false,
  clearable: undefined,
  isMultiple: false,
  width: null,
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
    extraProps.validate = validators.required;
    extraProps.required = true;
  }

  if (extraProps.validate && rest.validate) {
    extraProps.validate = validators.chain(extraProps.validate, rest.validate);
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
  required: PropTypes.bool,
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
  } else if (type === 'text' || type === 'email') {
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
  type: PropTypes.oneOf(['text', 'email', 'number']),
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
export function FinalTextArea({name, label, nullIfEmpty, ...rest}) {
  return (
    <FinalField
      name={name}
      label={label}
      component={TextArea}
      format={formatters.trim}
      formatOnBlur
      parse={nullIfEmpty ? parsers.nullIfEmpty : identity}
      {...rest}
    />
  );
}

FinalTextArea.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string,
  nullIfEmpty: PropTypes.bool,
};

FinalTextArea.defaultProps = {
  label: null,
  nullIfEmpty: false,
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
  label: PropTypes.string.isRequired,
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
 * A submit button that will update according to the final-form state.
 */
export function FinalSubmitButton({
  label,
  form,
  disabledUntilChange,
  activeSubmitButton,
  color,
  onClick,
  circular,
  size,
  icon,
  children,
}) {
  const {validating, hasValidationErrors, pristine, submitting} = useFormState({
    subscription: {validating: true, hasValidationErrors: true, pristine: true, submitting: true},
  });
  const disabled =
    validating || hasValidationErrors || (disabledUntilChange && pristine) || submitting;
  return (
    <Form.Field disabled={disabled}>
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
      />
      {children && children(disabled)}
    </Form.Field>
  );
}

FinalSubmitButton.propTypes = {
  label: PropTypes.string,
  form: PropTypes.string,
  disabledUntilChange: PropTypes.bool,
  activeSubmitButton: PropTypes.bool,
  color: PropTypes.string,
  onClick: PropTypes.func,
  circular: PropTypes.bool,
  icon: PropTypes.string,
  size: PropTypes.string,
  children: PropTypes.func,
};

FinalSubmitButton.defaultProps = {
  label: null,
  form: null,
  disabledUntilChange: true,
  activeSubmitButton: true,
  color: null,
  onClick: null,
  circular: false,
  icon: null,
  size: null,
  children: null,
};
