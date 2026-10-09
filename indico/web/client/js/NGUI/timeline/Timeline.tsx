// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {forwardRef} from 'react';

import './Timeline.module.scss';
import {Dot} from 'indico/NGUI/dot/Dot';
import {IndicoPaletteColor} from 'indico/NGUI/tokens';
import {NativeProps, sharedClassName} from 'indico/NGUI/utils';

interface TimelineTitleCustomProps {
  dotColor?: IndicoPaletteColor;
}

type TimelineTitleProps = TimelineTitleCustomProps & NativeProps<'h5'>;

export const TimelineTitle = (props: TimelineTitleProps) => {
  const {dotColor = 'primary', ...nativeProps} = props;
  return (
    <h5 className={sharedClassName(nativeProps.className)} styleName="timeline-title">
      <Dot styleName="dot" color={dotColor} size="sm" />
      {nativeProps.children}
    </h5>
  );
};

type TimelineContentProps = NativeProps<'div'>;

export const TimelineContent = (props: TimelineContentProps) => {
  const {...nativeProps} = props;
  return (
    <div
      {...nativeProps}
      styleName="timeline-content-wrapper"
      className={sharedClassName(nativeProps.className)}
    >
      <div styleName="line" />
      {nativeProps.children}
    </div>
  );
};

TimelineContent.displayName = 'TimelineContent';

type TimelineItemRootProps = NativeProps<'div'>;

const TimelineItemRoot = forwardRef<HTMLDivElement, TimelineItemRootProps>((props, ref) => {
  return (
    <div
      ref={ref}
      styleName="timeline-item"
      className={sharedClassName(props.className)}
      role="group"
    >
      {props.children}
    </div>
  );
});

TimelineItemRoot.displayName = 'TimelineItem';

type TimelineItemComponent = React.FunctionComponent<TimelineItemRootProps> & {
  Title: typeof TimelineTitle;
  Content: typeof TimelineContent;
};

export const TimelineItem = Object.assign(TimelineItemRoot, {
  Title: TimelineTitle,
  Content: TimelineContent,
}) as TimelineItemComponent;
