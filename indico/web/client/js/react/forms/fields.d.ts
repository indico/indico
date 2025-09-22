// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment/moment';
import {ComponentType} from 'react';

interface SharedFieldProps {
  name: string;
  description?: React.ReactNode;
  autoFocus?: boolean;
  required?: boolean | 'no-validator';
  disabled?: boolean;
}

interface FinalFieldProps extends SharedFieldProps {
  adapter?: ComponentType<any>;
  component?: ComponentType<any>;
  onChange?: (newValue: object, oldValue: object) => void;
  [key: string]: any;
}

interface FinalInputProps extends SharedFieldProps {
  label?: string | null;
  type?: 'text' | 'email' | 'number' | 'tel' | 'password';
  nullIfEmpty?: boolean;
  noAutoComplete?: boolean;
}

interface FinalTextAreaProps extends SharedFieldProps {
  label?: string | null;
  nullIfEmpty?: boolean;
  action?: object;
}

interface FinalCheckboxProps extends SharedFieldProps {
  label: string | React.ReactNode;
  value?: string;
}

interface FinalRadioProps extends SharedFieldProps {
  label: string | React.ReactNode;
  value: string;
}

interface FinalDropdownProps extends SharedFieldProps {
  options: object[];
  placeholder?: string;
  label?: string | null;
  multiple?: boolean;
  selection?: boolean;
  search?: boolean;
  nullIfEmpty?: boolean;
  parse?: (value: any) => any;
  format?: (value: any) => any;
}

interface FinalComboDropdownProps extends SharedFieldProps {
  label?: string | null;
  allowAdditions?: boolean;
}

interface FinalTimePickerProps extends SharedFieldProps {
  label?: string | null;
  defaultValue?: string;
}

interface FinalDurationProps extends SharedFieldProps {
  label?: string | null;
  defaultValue?: number;
  max?: number | null;
}

interface FinalDateTimePickerProps extends SharedFieldProps {
  label?: string | null;
  defaultValue?: string;
  minStartDt?: Moment;
  maxEndDt?: Moment;
}

interface FinalSubmitButtonProps {
  label?: string | null;
  form?: string | null;
  disabledUntilChange?: boolean;
  disabledIfInvalid?: boolean;
  disabledAfterSubmit?: boolean;
  activeSubmitButton?: boolean;
  color?: string | null;
  onClick?: (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => void;
  circular?: boolean;
  icon?: string | null;
  fluid?: boolean;
  size?: string | null;
  style?: object | null;
  extraSubscription?: object;
  children?:
    | ((props: {submitting: boolean; pristine: boolean; invalid: boolean}) => React.ReactNode)
    | null;
}

declare const FinalField: ComponentType<FinalFieldProps>,
  FinalInput: ComponentType<FinalInputProps>,
  FinalTextArea: ComponentType<FinalTextAreaProps>,
  FinalCheckbox: ComponentType<FinalCheckboxProps>,
  FinalRadio: ComponentType<FinalRadioProps>,
  FinalDropdown: ComponentType<FinalDropdownProps>,
  FinalComboDropdown: ComponentType<FinalComboDropdownProps>,
  FinalTimePicker: ComponentType<FinalTimePickerProps>,
  FinalDuration: ComponentType<FinalDurationProps>,
  FinalDateTimePicker: ComponentType<FinalDateTimePickerProps>,
  FinalSubmitButton: ComponentType<FinalSubmitButtonProps>;

export {
  FinalField,
  FinalInput,
  FinalTextArea,
  FinalCheckbox,
  FinalRadio,
  FinalDropdown,
  FinalComboDropdown,
  FinalTimePicker,
  FinalDuration,
  FinalDateTimePicker,
  FinalSubmitButton,
};
