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
export type Variant = 'solid' | 'light' | 'white';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ButtonOpacity = 'opaque' | 'transparent';
export type IconPosition = 'left' | 'right';

// export type ButtonVariant = 'outlined' | 'transparent' | 'opaque' | 'compact';

interface BaseButtonProps {
  color: ButtonColor;
  variant?: Variant;
  size?: ButtonSize;
  opacity?: ButtonOpacity;
  className?: string;
  disabled?: boolean;
  outlined?: boolean;
  compact?: boolean;
  icon?: IconSource;
  iconPosition?: IconPosition;
  onClick?: () => void;
  href?: string;
  children: React.ReactNode;
}

export type ButtonProps =
  | (BaseButtonProps & {
      variant: 'solid' | 'light' | 'white';
      opacity?: 'opaque';
    })
  | (BaseButtonProps & {
      variant?: never;
      opacity?: 'transparent';
    });

export default function Button(props: ButtonProps) {
  const {
    color = 'primary',
    variant = 'solid',
    size = 'md',
    opacity,
    className,
    disabled = false,
    outlined = false,
    compact = false,
    icon,
    iconPosition = 'left',
    onClick,
    href,
    children,
  } = props;

  return href ? (
    <a
      href={href}
      styleName="root"
      className={`indico-ui ${className || ''}`}
      data-color={color}
      data-variant={variant}
      data-size={size}
      data-opacity={opacity}
      data-disabled={disabled ? '' : undefined}
      data-outlined={outlined ? '' : undefined}
      data-compact={compact ? '' : undefined}
      onClick={onClick}
    >
      {iconPosition === 'left' && icon && (
        <Icon icon={icon} color={color} size={size} variant="compact" decorative />
      )}
      {children}
      {iconPosition === 'right' && icon && (
        <Icon icon={icon} color={color} size={size} variant="compact" decorative />
      )}
    </a>
  ) : (
    <button
      type="button"
      styleName="root"
      className={`indico-ui ${className || ''}`}
      data-color={color}
      data-variant={variant}
      data-size={size}
      data-opacity={opacity}
      data-disabled={disabled ? '' : undefined}
      data-outlined={outlined ? '' : undefined}
      data-compact={compact ? '' : undefined}
      onClick={onClick}
    >
      {iconPosition === 'left' && icon && (
        <Icon icon={icon} color={color} size={size} variant="compact" decorative />
      )}
      {children}
      {iconPosition === 'right' && icon && (
        <Icon icon={icon} color={color} size={size} variant="compact" decorative />
      )}
    </button>
  );
}
// TO DO: white on white allow only if with opaque or transparent bg
