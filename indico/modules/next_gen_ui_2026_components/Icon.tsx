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

type IconSource =
  | {
      name: IconName;
      prefix?: IconPrefix;
    }
  | {
      svg: React.ReactNode;
    };

export type IconColor = 'primary' | 'gray' | 'success' | 'warning' | 'error';
export type IconVariant = 'light' | 'solid' | 'dark' | 'plain';
export type IconSize = 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface IconProps {
  icon: IconSource;
  styleName?: string;
  color?: IconColor;
  size?: IconSize;
  variant?: IconVariant;
  rounded?: boolean;
  ariaLabel?: string;
  title?: string;
}

export const Icon: React.FC<IconProps> = ({
  icon,
  styleName,
  color = 'primary',
  size = 'md',
  variant = 'plain',
  rounded = false,
  ariaLabel,
  title,
}) => {
  const decorative = !ariaLabel;

  return (
    <span
      styleName={`root ${styleName || ''}`}
      data-color={color}
      data-size={size}
      data-variant={variant}
      data-rounded={rounded ? '' : undefined}
      title={title} // TODO: remake this into new tooltip component
      aria-hidden={decorative}
      role={decorative ? undefined : 'img'}
      aria-label={ariaLabel}
    >
      {'svg' in icon ? (
        icon.svg
      ) : (
        <FontAwesomeIcon
          icon={{
            prefix: icon.prefix ?? 'fas',
            iconName: icon.name,
          }}
        />
      )}
    </span>
  );
};
