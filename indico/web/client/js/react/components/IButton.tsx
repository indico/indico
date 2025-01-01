// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {toClasses} from 'indico/react/util';

interface IButtonPropTypes {
  classes: object;
  href: string | undefined;
  title: string;
  children: React.ReactNode;
  onClick: (() => undefined) | undefined;
  highlight: boolean;
  disabled: boolean;
  icon: string;
  dropdown: boolean;
  borderless: boolean;
  style: object;
}

/** Legacy-style Indico UI Button */
export default function IButton({
  classes = {},
  href,
  title,
  children,
  onClick,
  highlight = false,
  disabled = false,
  icon = '',
  dropdown = false,
  borderless = false,
  style = {},
}: IButtonPropTypes) {
  const finalClasses: Record<string, boolean> = {
    ...classes,
    'i-button': true,
    disabled,
    highlight,
    borderless,
  };

  if (icon) {
    finalClasses[`icon-${icon}`] = true;
  }

  if (dropdown) {
    finalClasses['arrow'] = true;
  }

  const attrs: Record<string, string | object | (() => undefined)> = {
    title,
    style,
    className: toClasses(finalClasses),
  };

  if (!disabled && onClick) {
    attrs['onClick'] = onClick;
  }

  if (href) {
    return (
      <a href={href} {...attrs}>
        {children}
      </a>
    );
  } else {
    return (
      <button type="button" {...attrs}>
        {children}
      </button>
    );
  }
}
