// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import './Timeline.module.scss';

export type TimelineItemDotColor = 'primary' | 'gray' | 'success' | 'warning' | 'error';

interface TimelineTitleProps {
  dotColor?: TimelineItemDotColor;
  children: React.ReactNode;
  className?: string;
}

export const TimelineTitle = ({children, className, dotColor = 'primary'}: TimelineTitleProps) => (
  <h5 className={className ?? ''}>
    <span styleName="dot" data-color={dotColor} />
    {children}
  </h5>
);

interface TimelineContentProps {
  children: React.ReactNode;
  className?: string;
}

export const TimelineContent = ({children, className}: TimelineContentProps) => (
  <div styleName="timeline-content-wrapper" className={className ?? ''}>
    <div styleName="line" />
    {children}
  </div>
);

interface TimelineItemProps {
  className?: string;
  children: React.ReactNode;
}

const TimelineItemRoot = ({className, children}: TimelineItemProps) => (
  <div styleName="timeline-item" className={`indico-ui ${className || ''}`} role="group">
    {children}
  </div>
);

type TimelineItemComponent = React.FunctionComponent<TimelineItemProps> & {
  Title: typeof TimelineTitle;
  Content: typeof TimelineContent;
};

export const TimelineItem = Object.assign(TimelineItemRoot, {
  Title: TimelineTitle,
  Content: TimelineContent,
}) as TimelineItemComponent;
