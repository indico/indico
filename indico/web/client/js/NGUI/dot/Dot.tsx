// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {IndicoPaletteColor, LegacyColor, Size} from 'indico/NGUI/tokens';
import {sharedClassName, NativeProps} from 'indico/NGUI/utils';
import './Dot.module.scss';

export type DotColor = IndicoPaletteColor | LegacyColor;

interface CustomDotProps {
  color?: DotColor;
}

export type DotSizeLabelMaxValueUnion =
  | {label?: string; size?: Exclude<Size, 'xs'>; maxValue?: never}
  | {label?: number; size?: Exclude<Size, 'xs'>; maxValue?: number}
  | {label?: never; size: 'xs'; maxValue?: never};

export type DotProps = CustomDotProps & DotSizeLabelMaxValueUnion & NativeProps<'span'>;

export const Dot = forwardRef<HTMLSpanElement, DotProps>((props, ref) => {
  const {color = 'primary', size = 'md', label, maxValue, ...nativeProps} = props;
  const formattedLabel =
    maxValue !== undefined && typeof label === 'number' && label > maxValue
      ? `${maxValue}+`
      : label;

  return (
    <span
      {...nativeProps}
      ref={ref}
      styleName="dot"
      className={sharedClassName(nativeProps.className)}
      data-color={color}
      data-size={size}
      data-label={!!label}
    >
      {formattedLabel}
    </span>
  );
});

Dot.displayName = 'Dot';
