// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Icon, IconSource} from '../icon/Icon';
import {IconPosition, IndicoPaletteColor, LegacyColor, Size, TextWeight, Variant} from '../tokens';
import {NativeProps} from '../utils';

import './Tag.module.scss';

export type TagColorMerged = IndicoPaletteColor | LegacyColor;
export type TagVariant = Variant;
export type TagSize = Size;
export type TagTextWeight = TextWeight;

export interface CustomTagProps {
  className?: string;
  variant?: TagVariant;
  size?: TagSize;
  textWeight?: TagTextWeight;
  outlined?: boolean;
  rounded?: boolean;
  opaque?: boolean;
  icon?: IconSource;
  iconPosition?: IconPosition;
  onIconClick?: React.MouseEventHandler<HTMLSpanElement>;
  children?: React.ReactNode;
}

type NativeSpanProps = NativeProps<'span'>;

export type TagProps = CustomTagProps &
  NativeSpanProps &
  (
    | {
        variant?: 'transparent' | 'white';
        color?: TagColorMerged;
        opaque?: never;
      }
    | {
        variant?: 'solid' | 'light';
        color?: IndicoPaletteColor;
        opaque?: boolean;
      }
  );

export const Tag = forwardRef<HTMLSpanElement, TagProps>((props, ref) => {
  const {
    className,
    color = 'primary',
    variant = 'solid',
    size = 'md',
    textWeight = 'medium',
    outlined = false,
    rounded = true,
    opaque = false,
    icon,
    iconPosition = 'left',
    ...nativeProps
  } = props;

  const sharedClassName = `indico-ui ${className || ''}`;

  const dataProps = {
    'data-color': color,
    'data-variant': variant,
    'data-size': size,
    'data-text-weight': textWeight,
    'data-outlined': outlined ? '' : undefined,
    'data-rounded': rounded ? '' : undefined,
    'data-opaque': opaque ? '' : undefined,
    'data-icon': icon ? '' : undefined,
    'data-icon-position': iconPosition,
  };

  const iconElement = icon && (
    <Icon
      icon={icon}
      data-clickable={!!props.onIconClick}
      onClick={props.onIconClick}
      variant="compact"
      decorative
      styleName="tag-icon"
    />
  );

  const content = (
    <>
      {icon && iconPosition !== 'right' && iconElement}
      {nativeProps.children}
      {icon && iconPosition === 'right' && iconElement}
    </>
  );

  return (
    <span
      ref={ref as React.Ref<HTMLSpanElement>}
      styleName="tag"
      data-clickable={false}
      className={sharedClassName}
      {...dataProps}
      {...nativeProps}
    >
      {content}
    </span>
  );
});

Tag.displayName = 'Tag';
