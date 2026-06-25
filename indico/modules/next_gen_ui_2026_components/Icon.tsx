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
import React from 'react';

import './Icon.module.scss';

library.add(fas, far, fab);

type IconSource = string | React.ComponentType<React.SVGProps<SVGSVGElement>>;

export type IconColor = 'primary' | 'gray' | 'success' | 'warning' | 'error';
export type IconVariant = 'light' | 'solid' | 'dark' | 'plain' | 'compact';
export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface IconProps {
  icon: IconSource;
  className?: string;
  color?: IconColor;
  size?: IconSize;
  variant?: IconVariant;
  rounded?: boolean;
  ariaLabel?: string;
  title?: string;
}

function isCustomIcon(
  icon: IconSource
): icon is React.ComponentType<React.SVGProps<SVGSVGElement>> {
  return typeof icon !== 'string';
}

function parseIconString(icon: string): {
  prefix: IconPrefix;
  iconName: IconName;
};

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

export const Icon = (props: IconProps) => {
  const {
    icon,
    className,
    color = 'primary',
    size = 'md',
    variant = 'plain',
    rounded = false,
    ariaLabel,
    title,
  } = props;

  let content: React.ReactNode;

  if (isCustomIcon(icon)) {
    const SvgIcon = icon;

    content = <SvgIcon focusable="false" aria-hidden="true" />;
  } else {
    const {prefix, iconName} = parseIconString(icon);

    content = (
      <FontAwesomeIcon
        icon={{
          prefix,
          iconName,
        }}
        focusable="false"
      />
    );
  }

  // console.log(props);

  console.log('className', className);
  console.log('styleName', 'root');
  // console.log("ariaLabel", ariaLabel);

  return (
    <span
      styleName="root"
      className={className}
      data-color={color}
      data-size={size}
      data-variant={variant}
      data-rounded={rounded ? '' : undefined}
      title={title}
      aria-hidden={!ariaLabel}
      aria-label={ariaLabel}
    >
      {content}
    </span>
  );

  // );
  // {'svg' in icon ? (
  //   icon.svg
  // ) : (
  //   <FontAwesomeIcon
  //     icon={{
  //       prefix: icon.prefix ?? 'fas',
  //       iconName: icon.name,
  //     }}
  //     focusable="false"
  //   />
  // )}
};
