// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {IndicoPaletteColor, LegacyColor} from '../tokens';
import {sharedClassName, NativeProps} from '../utils';
import './Dot.module.scss';

export type DotColor = IndicoPaletteColor | LegacyColor;

interface CustomDotProps {
  color?: DotColor;
  size?: string;
}

export type DotProps = CustomDotProps & NativeProps<'span'>;

export const Dot = forwardRef<HTMLSpanElement, DotProps>((props, ref) => {
  const {color = 'primary', size = 'md', ...nativeProps} = props;

  return (
    <span
      {...nativeProps}
      ref={ref}
      styleName="dot"
      className={sharedClassName(nativeProps.className)}
      data-color={color}
      data-size={size}
    />
  );
});

Dot.displayName = 'Dot';
