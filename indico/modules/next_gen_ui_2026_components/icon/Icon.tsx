// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {IconName, IconPrefix, library} from '@fortawesome/fontawesome-svg-core';
import {fab} from '@fortawesome/free-brands-svg-icons';
import {far} from '@fortawesome/free-regular-svg-icons';
import {fas} from '@fortawesome/free-solid-svg-icons';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import React, {forwardRef} from 'react';

import './Icon.module.scss';
import {ExtendedIndicoPaletteColor, Size} from '../tokens';
import {NativeProps} from '../utils';

library.add(fas, far, fab);

export type IconSource = string | React.ComponentType<React.SVGProps<SVGSVGElement>>;
export type IconColor = ExtendedIndicoPaletteColor;
export type IconVariant = 'light' | 'solid' | 'dark' | 'plain' | 'compact';
export type IconSize = Size;

interface CustomIconProps {
  icon: IconSource;
  className?: string;
  color?: IconColor;
  size?: IconSize;
  variant?: IconVariant;
  rounded?: boolean;
  decorative?: boolean;
  ariaLabel?: string;
  onClick?: React.MouseEventHandler<HTMLSpanElement>;
}

type VariantUnion =
  | {
      variant?: 'light' | 'solid' | 'dark';
      rounded?: boolean;
      color?: 'primary' | 'gray' | 'success' | 'warning' | 'error';
    }
  | {
      variant?: 'plain' | 'compact';
      rounded?: never;
      color?: 'primary' | 'gray' | 'success' | 'warning' | 'error' | 'white';
    };

export type IconProps = CustomIconProps & NativeProps<'span', 'onClick'> & VariantUnion;

function isCustomIcon(
  icon: IconSource
): icon is React.ComponentType<React.SVGProps<SVGSVGElement>> {
  return typeof icon !== 'string';
}

function parseIconString(icon: string): {
  prefix: IconPrefix;
  iconName: IconName;
} {
  const [prefix, iconName] = icon.split(':');

  return {
    prefix: (prefix as IconPrefix) || 'fas',
    iconName: iconName as IconName,
  };
}

export const Icon = forwardRef<HTMLSpanElement | HTMLAnchorElement, IconProps>((props, ref) => {
  const {
    icon,
    className,
    color = 'primary',
    size = 'md',
    variant = 'plain',
    rounded = false,
    decorative = true,
    ariaLabel,
    title,
    ...nativeProps
  } = props;

  const isDecorative = decorative || !ariaLabel;
  let content: React.ReactNode;

  if (isCustomIcon(icon)) {
    const SvgIcon = icon;
    content = <SvgIcon className="indico-ui" focusable="false" aria-hidden="true" />;
  } else {
    const {prefix, iconName} = parseIconString(icon);
    content = (
      <FontAwesomeIcon
        icon={{
          prefix,
          iconName,
        }}
        focusable="false"
        aria-hidden="true"
      />
    );
  }

  const dataProps = {
    'data-color': color,
    'data-size': size,
    'data-variant': variant,
    'data-rounded': rounded ? '' : undefined,
    'aria-hidden': isDecorative,
    'aria-label': !isDecorative ? ariaLabel : undefined,
  };

  return (
    <span
      ref={ref as React.Ref<HTMLSpanElement>}
      styleName="root"
      className={`indico-ui ${className || ''}`}
      title={title}
      {...dataProps}
      {...nativeProps}
    >
      {content}
    </span>
  );
});

Icon.displayName = 'Icon';
