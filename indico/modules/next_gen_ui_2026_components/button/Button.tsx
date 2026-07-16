// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import React from 'react';

import {Icon, IconSource} from '../icon/Icon';

import './Button.module.scss';

export type ButtonColor = 'primary' | 'gray' | 'success' | 'warning' | 'error' | 'white';
export type ButtonVariant = 'solid' | 'light' | 'white' | 'transparent';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ButtonTextWeight = 'regular' | 'medium' | 'semibold' | 'bold';
export type IconPosition = 'left' | 'right' | 'icon-only';

interface BaseButtonProps {
  className?: string;
  color: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  textWeight?: ButtonTextWeight;
  opaque?: boolean;
  disabled?: boolean;
  outlined?: boolean;
  compact?: boolean;
  animated?: boolean;
  rounded?: boolean;
  icon?: IconSource;
  iconPosition?: IconPosition;
  onClick?: () => void;
  href?: string;
  children?: React.ReactNode;
}

export type ButtonProps = BaseButtonProps &
  (
    | {
        variant: 'transparent';
        color?: ButtonColor;
        opaque?: never;
      }
    | {
        variant: 'solid' | 'light' | 'white';
        color: Exclude<ButtonColor, 'white'>;
        opaque?: boolean;
      }
  );

export default function Button(props: ButtonProps) {
  const {
    className,
    color = 'primary',
    variant = 'solid',
    size = 'md',
    textWeight = 'regular',
    disabled = false,
    opaque = false,
    outlined = false,
    compact = false,
    animated = false,
    rounded = false,
    icon,
    iconPosition = 'left',
    onClick,
    href,
    children,
  } = props;

  return href ? (
    <a
      href={href}
      styleName="button"
      className={`indico-ui ${className || ''}`}
      data-color={color}
      data-variant={variant}
      data-size={size}
      data-text-weight={textWeight}
      data-disabled={disabled ? '' : undefined}
      data-opaque={opaque ? '' : undefined}
      data-outlined={outlined ? '' : undefined}
      data-compact={compact ? '' : undefined}
      data-animated={animated ? '' : undefined}
      data-rounded={rounded ? '' : undefined}
      data-icon={icon ? '' : undefined}
      data-icon-position={iconPosition}
      onClick={onClick}
    >
      {(iconPosition === 'left' || iconPosition === 'icon-only') && icon && (
        <Icon icon={icon} variant="compact" decorative styleName="button-icon" />
      )}
      {children}
      {iconPosition === 'right' && icon && (
        <Icon icon={icon} variant="compact" decorative styleName="button-icon" />
      )}
    </a>
  ) : (
    <button
      type="button"
      styleName="button"
      className={`indico-ui ${className || ''}`}
      data-color={color}
      data-variant={variant}
      data-size={size}
      data-text-weight={textWeight}
      data-disabled={disabled ? '' : undefined}
      data-opaque={opaque ? '' : undefined}
      data-outlined={outlined ? '' : undefined}
      data-compact={compact ? '' : undefined}
      data-animated={animated ? '' : undefined}
      data-rounded={rounded ? '' : undefined}
      data-icon={icon ? '' : undefined}
      data-icon-position={iconPosition}
      onClick={onClick}
    >
      {(iconPosition === 'left' || iconPosition === 'icon-only') && icon && (
        <Icon icon={icon} variant="compact" decorative styleName="button-icon" />
      )}
      {children}
      {iconPosition === 'right' && icon && (
        <Icon icon={icon} variant="compact" decorative styleName="button-icon" />
      )}
    </button>
  );
}
