// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Icon, IconSource} from 'indico/NGUI/icon/Icon';

import './Button.module.scss';
import {
  ExtendedIndicoPaletteColor,
  IconPosition,
  IndicoPaletteColor,
  Size,
  TextWeight,
  Variant,
} from '../tokens';
import {guardDisabledClick, sharedClassName, NativeProps} from '../utils';

// TODO: Add support for loading state (spinner)

export type ButtonColor = IndicoPaletteColor;
export type ButtonVariant = Variant;
export type ButtonSize = Exclude<Size, 'xxs'>;
export type ButtonTextWeight = TextWeight;
export type ButtonIconPosition = IconPosition;

interface CustomButtonProps {
  className?: string;
  size?: ButtonSize;
  textWeight?: ButtonTextWeight;
  opaque?: boolean;
  disabled?: boolean;
  loading?: boolean;
  outlined?: boolean;
  compact?: boolean;
  animated?: boolean;
  rounded?: boolean;
  circular?: boolean;
  squared?: boolean;
  fullWidth?: boolean;
  active?: boolean;
  icon?: IconSource;
  iconPosition?: ButtonIconPosition;
  iconOnly?: boolean;
}

type NativeButtonProps = NativeProps<'button'>;
type NativeAnchorProps = NativeProps<'a'>;
type NativeUnion = ({href?: undefined} & NativeButtonProps) | ({href: string} & NativeAnchorProps);

type RoundnessUnion = {rounded?: boolean; circular?: never} | {rounded?: never; circular?: boolean};

type SquaredUnion = {squared: boolean; rounded?: never; circular?: never} | {squared?: never};

type VariantColorUnion =
  | {variant?: 'transparent'; color?: ExtendedIndicoPaletteColor; opaque?: never}
  | {
      variant?: 'solid' | 'light' | 'white';
      color?: IndicoPaletteColor;
      opaque?: boolean;
    };

type IconOnlyUnion =
  | {
      icon?: IconSource;
      iconPosition?: 'left' | 'right';
      children?: React.ReactNode;
      iconOnly?: false;
    }
  | {
      icon: IconSource;
      iconOnly: true;
      children?: never;
      'aria-label': string;
      iconPosition?: never;
    };

export type ButtonProps = CustomButtonProps &
  NativeUnion &
  VariantColorUnion &
  IconOnlyUnion &
  RoundnessUnion &
  SquaredUnion;

export const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, ButtonProps>(
  (props, ref) => {
    const {
      className,
      color = 'primary',
      variant = 'solid',
      size = 'md',
      textWeight = 'bold',
      disabled = false,
      loading = false,
      opaque = false,
      outlined = false,
      compact = false,
      animated = false,
      rounded = false,
      circular = false,
      squared = false,
      fullWidth = false,
      active = false,
      icon,
      iconPosition = 'left',
      iconOnly = false,
      ...nativeProps
    } = props;

    const handleClick = guardDisabledClick<HTMLButtonElement | HTMLAnchorElement>(
      disabled,
      nativeProps.onClick,
      loading
    );

    const dataProps = {
      'data-color': color,
      'data-variant': variant,
      'data-size': size,
      'data-text-weight': textWeight,
      'data-disabled': disabled ? '' : undefined,
      'data-loading': loading ? '' : undefined,
      'data-opaque': opaque ? '' : undefined,
      'data-outlined': outlined ? '' : undefined,
      'data-compact': compact ? '' : undefined,
      'data-animated': animated ? '' : undefined,
      'data-rounded': rounded ? '' : undefined,
      'data-circular': circular ? '' : undefined,
      'data-squared': squared ? '' : undefined,
      'data-full-width': fullWidth ? '' : undefined,
      'data-active': active ? '' : undefined,
      'data-icon': icon ? '' : undefined,
      'data-icon-position': iconPosition,
      'data-icon-only': iconOnly ? '' : undefined,
    };

    const iconElement = icon && (
      <Icon
        icon={icon}
        variant="transparent"
        compact
        size={size}
        decorative
        styleName="button-icon"
      />
    );

    // if content has no children but has an icon, aria-label is required for accessibility
    const content = (
      <>
        {icon && iconPosition !== 'right' && iconElement}
        {nativeProps.children}
        {icon && iconPosition === 'right' && iconElement}
      </>
    );

    if (nativeProps.href !== undefined) {
      const rest = nativeProps as NativeAnchorProps;
      return (
        <a
          {...rest}
          {...dataProps}
          ref={ref as React.Ref<HTMLAnchorElement>}
          styleName="button"
          className={sharedClassName(className)}
          href={disabled || loading ? undefined : rest.href}
          aria-disabled={disabled || loading || undefined}
          aria-busy={loading || undefined}
          onClick={handleClick}
          role={disabled || loading ? undefined : 'button'}
        >
          {content}
        </a>
      );
    }

    const rest = nativeProps as NativeButtonProps;
    return (
      <button
        {...rest}
        {...dataProps}
        ref={ref as React.Ref<HTMLButtonElement>}
        type="button"
        styleName="button"
        className={sharedClassName(className)}
        disabled={disabled || loading}
        onClick={handleClick}
        aria-disabled={disabled || loading || undefined}
        aria-busy={loading || undefined}
      >
        {content}
      </button>
    );
  }
);

Button.displayName = 'Button';
