// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import {Dot, DotProps} from 'indico/NGUI/dot/Dot';
import {sharedClassName, NativeProps} from 'indico/NGUI/utils';

import './Indicator.module.scss';

export type IndicatorPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';

export interface CustomIndicatorProps {
  position?: IndicatorPosition;
}

type NativeDivProps = NativeProps<'div'>;

export type IndicatorProps = CustomIndicatorProps & NativeDivProps & DotProps;

export const Indicator = forwardRef<HTMLDivElement, IndicatorProps>((props, ref) => {
  const {position = 'top-right', ...dotProps} = props;

  return (
    <div
      {...dotProps}
      ref={ref as React.Ref<HTMLDivElement>}
      styleName="indicator-root"
      data-clickable={false}
      className={sharedClassName(dotProps.className)}
      data-position={position}
    >
      <Dot {...dotProps} styleName="indicator-dot" />
    </div>
  );
});

Indicator.displayName = 'Indicator';
