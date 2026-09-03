// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

export type NativeProps<
  Tag extends keyof React.JSX.IntrinsicElements,
  Omitted extends string = never,
> = Omit<React.ComponentPropsWithoutRef<Tag>, Omitted>;

export function guardDisabledClick<E extends HTMLElement>(
  disabled?: boolean,
  onClick?: (event: React.MouseEvent<E>) => void,
  loading?: boolean
) {
  return (event: React.MouseEvent<E>) => {
    if (disabled || loading) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    onClick?.(event);
  };
}

export const sharedClassName = (className?: string) => `indico-ui ${className || ''}`;
