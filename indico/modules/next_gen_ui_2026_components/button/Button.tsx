// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Icon, IconSource} from '../icon/Icon';
import './Button.module.scss';
import {guardDisabledClick, NativeProps} from '../utils';

// TODO: Add support for loading state (spinner)

export type ButtonColor = 'primary' | 'gray' | 'success' | 'warning' | 'error' | 'white';
export type ButtonVariant = 'solid' | 'light' | 'white' | 'transparent';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type ButtonTextWeight = 'regular' | 'medium' | 'semibold' | 'bold';
export type IconPosition = 'left' | 'right' | 'icon-only';

interface CustomButtonProps {
  className?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  textWeight?: ButtonTextWeight;
  opaque?: boolean;
  disabled?: boolean;
  loading?: boolean;
  outlined?: boolean;
  compact?: boolean;
  animated?: boolean;
  rounded?: boolean;
  fullWidth?: boolean;
  icon?: IconSource;
  iconPosition?: IconPosition;
  // onClick?: (event: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => void;
}

// type NativeButtonProps =
//   React.ButtonHTMLAttributes<HTMLButtonElement>
// ;
// type NativeAnchorProps =
//   React.AnchorHTMLAttributes<HTMLAnchorElement>
// ;

type NativeButtonProps = NativeProps<'button'>;
type NativeAnchorProps = NativeProps<'a'>;

type hrefUnion = ({href?: undefined} & NativeButtonProps) | ({href: string} & NativeAnchorProps);

type VariantColorUnion =
  | {variant?: 'transparent'; color?: ButtonColor; opaque?: never}
  | {
      variant?: 'solid' | 'light' | 'white';
      color?: Exclude<ButtonColor, 'white'>;
      opaque?: boolean;
    };

type IconOnlyUnion =
  | {icon?: IconSource; iconPosition?: 'left' | 'right'; children?: React.ReactNode}
  | {icon: IconSource; iconPosition: 'icon-only'; children?: never; 'aria-label': string};

export type ButtonProps = CustomButtonProps & hrefUnion & VariantColorUnion & IconOnlyUnion;

const Button = forwardRef<HTMLButtonElement | HTMLAnchorElement, ButtonProps>((props, ref) => {
  const {
    className,
    color = 'primary',
    variant = 'solid',
    size = 'md',
    textWeight = 'semibold',
    disabled = false,
    loading = false,
    opaque = false,
    outlined = false,
    compact = false,
    animated = false,
    rounded = false,
    fullWidth = false,
    icon,
    iconPosition = 'left',
    // onClick,
    // children,
    ...nativeProps
  } = props;

  const handleClick = guardDisabledClick<HTMLButtonElement | HTMLAnchorElement>(
    disabled,
    nativeProps.onClick,
    loading
  );

  // const handleClick = (event: React.MouseEvent<HTMLButtonElement | HTMLAnchorElement>) => {
  //   if (disabled || loading) {
  //     event.preventDefault();
  //     return;
  //   }
  //   onClick?.(event);
  // };

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
    'data-full-width': fullWidth ? '' : undefined,
    'data-icon': icon ? '' : undefined,
    'data-icon-position': iconPosition,
  };

  const iconElement = icon && (
    <Icon icon={icon} variant="compact" decorative styleName="button-icon" />
  );

  // if content has no children but has an icon, aria-label is required for accessibility
  const content = (
    <>
      {icon && iconPosition !== 'right' && iconElement}
      {nativeProps.children}
      {icon && iconPosition === 'right' && iconElement}
    </>
  );

  const sharedClassName = `indico-ui ${className || ''}`;

  if (nativeProps.href !== undefined) {
    const rest = nativeProps as NativeAnchorProps;
    return (
      <a
        ref={ref as React.Ref<HTMLAnchorElement>}
        styleName="button"
        className={sharedClassName}
        href={disabled ? undefined : nativeProps.href}
        aria-disabled={disabled || loading || undefined}
        tabIndex={disabled || loading ? -1 : rest.tabIndex}
        aria-busy={loading || undefined}
        onClick={handleClick}
        {...dataProps}
        {...rest}
      >
        {content}
      </a>
    );
  }

  const rest = nativeProps as NativeButtonProps;
  return (
    <button
      ref={ref as React.Ref<HTMLButtonElement>}
      type="button"
      styleName="button"
      className={sharedClassName}
      disabled={disabled}
      onClick={handleClick}
      aria-disabled={disabled || loading || undefined}
      tabIndex={disabled || loading ? -1 : rest.tabIndex}
      aria-busy={loading || undefined}
      {...dataProps}
      {...rest}
    >
      {content}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;
