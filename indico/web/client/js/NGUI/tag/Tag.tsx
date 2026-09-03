// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Icon, IconSource} from 'indico/NGUI/icon/Icon';
import {
  IconPosition,
  IndicoPaletteColor,
  LegacyColor,
  Size,
  TextWeight,
  Variant,
} from 'indico/NGUI/tokens';
import {NativeProps, sharedClassName} from 'indico/NGUI/utils';

import './Tag.module.scss';

export type TagColorMerged = IndicoPaletteColor | LegacyColor;
export type TagVariant = Variant;
export type TagSize = Size;
export type TagTextWeight = TextWeight;

export interface CustomTagProps {
  className?: string;
  color?: TagColorMerged;
  size?: TagSize;
  textWeight?: TagTextWeight;
  outlined?: boolean;
  rounded?: boolean;
  opaque?: boolean;
  icon?: IconSource;
  iconPosition?: IconPosition;
}

type VariantUnion =
  | {
      variant?: 'transparent' | 'white';
      opaque?: never;
    }
  | {
      variant?: 'solid' | 'light';
      opaque?: boolean;
    };

export type TagProps = VariantUnion & CustomTagProps & NativeProps<'span'>;

export const Tag = forwardRef<HTMLSpanElement, TagProps>((props, ref) => {
  const {
    className,
    color = 'primary',
    variant = 'solid',
    size = 'md',
    textWeight = 'regular',
    outlined = false,
    rounded = false,
    opaque = false,
    icon,
    iconPosition = 'left',
    ...nativeProps
  } = props;

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
    <Icon icon={icon} compact decorative size={size} styleName="tag-icon" />
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
      {...nativeProps}
      {...dataProps}
      ref={ref as React.Ref<HTMLSpanElement>}
      styleName="tag"
      data-clickable={false}
      className={sharedClassName(className)}
    >
      {content}
    </span>
  );
});

Tag.displayName = 'Tag';
