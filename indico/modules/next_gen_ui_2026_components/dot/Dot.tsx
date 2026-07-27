// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {IndicoPaletteColor, LegacyColor} from '../tokens';

import './Dot.module.scss';

export type DotColor = IndicoPaletteColor | LegacyColor;

export const Dot = ({
  color = 'primary',
  size = 'md',
  className,
}: {
  color?: DotColor;
  size?: string;
  className?: string;
}) => (
  <span
    styleName="dot"
    className={`indico-ui ${className || ''}`}
    data-color={color}
    data-size={size}
  />
);
