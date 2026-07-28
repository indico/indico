// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {IndicoPaletteColor, LegacyColor} from '../tokens';

import './Dot.module.scss';

export type DotColor = IndicoPaletteColor | LegacyColor;

interface DotProps {
  color?: DotColor;
  size?: string;
  className?: string;
}

export const Dot = forwardRef<HTMLSpanElement, DotProps>(
  ({color = 'primary', size = 'md', className}, ref) => (
    <span
      ref={ref}
      styleName="dot"
      className={`indico-ui ${className || ''}`}
      data-color={color}
      data-size={size}
    />
  )
);

Dot.displayName = 'Dot';
