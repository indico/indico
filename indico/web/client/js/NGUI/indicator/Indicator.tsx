// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Dot} from 'indico/NGUI/dot/Dot';
import {IndicoPaletteColor, LegacyColor, Size, TextWeight, Variant} from 'indico/NGUI/tokens';
import {sharedClassName, NativeProps} from 'indico/NGUI/utils';

import './Indicator.module.scss';

export type IndicatorColorMerged = IndicoPaletteColor | LegacyColor;
export type IndicatorVariant = Variant;
export type IndicatorSize = Size;
export type IndicatorTextWeight = TextWeight;
export type IndicatorPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';

export interface CustomIndicatorProps {
  className?: string;
  variant?: IndicatorVariant;
  size?: IndicatorSize;
  color?: IndicatorColorMerged;
  position?: IndicatorPosition;
}

type NativeDivProps = NativeProps<'div'>;

export type IndicatorProps = CustomIndicatorProps & NativeDivProps;

export const Indicator = forwardRef<HTMLDivElement, IndicatorProps>((props, ref) => {
  const {className, color = 'primary', size = 'md', position = 'top-right', ...nativeProps} = props;

  return (
    <div
      {...nativeProps}
      ref={ref as React.Ref<HTMLDivElement>}
      styleName="indicator-root"
      data-clickable={false}
      className={sharedClassName(className)}
      data-color={color}
      data-size={size}
      data-position={position}
      title="" // title will be passed to the dot, not the indicator root
    >
      <Dot color={color} size={size} title={nativeProps.title} styleName="indicator-dot" />
      {nativeProps.children}
    </div>
  );
});

Indicator.displayName = 'Indicator';
