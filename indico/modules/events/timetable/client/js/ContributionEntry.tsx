// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useRef, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import * as actions from './actions';
import {ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {formatTimeRange} from './i18n';
import ResizeHandle from './ResizeHandle';
import {ContribEntry, BreakEntry} from './types';
import {minutesToPixels, pixelsToMinutes, snapPixels, snapMinutes} from './utils';

import './ContributionEntry.module.scss';
import './DayTimetable.module.scss';

interface _DraggableEntryProps {
  selected: boolean;
  setDuration: (duration: number) => void;
  parentEndDt?: moment.Moment;
}

type DraggableEntryProps = _DraggableEntryProps & (ContribEntry | BreakEntry);

export default function ContributionEntry({
  type,
  id,
  startDt,
  duration: _duration,
  title,
  blockRef,
  sessionId,
  textColor,
  backgroundColor,
  selected,
  x,
  y,
  listeners,
  setNodeRef,
  transform,
  isDragging,
  width,
  column,
  maxColumn,
  setDuration: _setDuration,
  parentEndDt,
}: DraggableEntryProps) {
  const dispatch = useDispatch();
  const resizeStartRef = useRef<number | null>(null);
  const [isResizing, setIsResizing] = useState(false);
  const [duration, setDuration] = useState(_duration);
  const sessionData = useSelector(state => state.sessions[sessionId]);
  let style: Record<string, string | number | undefined> = transform
    ? {
        transform: `translate3d(${transform.x}px, ${snapPixels(transform.y)}px, 10px)`,
        // zIndex: 70,
      }
    : {};
  style = {
    ...style,
    position: 'absolute',
    top: y,
    left: x,
    width: `calc(${width} - 6px)`,
    height: minutesToPixels(Math.max(duration, minutesToPixels(5)) - 2),
    zIndex: isDragging || isResizing ? 1000 : selected ? 80 : style.zIndex,
    cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
    filter: selected ? 'drop-shadow(0 0 2px #000)' : undefined,
    backgroundColor: backgroundColor
      ? backgroundColor
      : sessionData
      ? ENTRY_COLORS_BY_BACKGROUND[sessionData.backgroundColor].childColor
      : '#5b1aff',
    color: textColor ? textColor : sessionData ? sessionData.textColor : undefined,
  };

  const deltaMinutes = snapMinutes(pixelsToMinutes(transform ? transform.y : 0));
  const newStart = moment(startDt).add(deltaMinutes, 'minutes');
  const newEnd = moment(startDt).add(deltaMinutes + duration, 'minutes');

  const timeRange = formatTimeRange('en', newStart, newEnd); // TODO: use current locale

  useEffect(() => {
    setDuration(_duration);
  }, [_duration]);

  useEffect(() => {
    const elem = (blockRef || {}).current;

    // TODO: This is not the nicest solution..
    if (elem) {
      if (isDragging || isResizing) {
        elem.style.zIndex = 1000;
      } else if (!isDragging && !isResizing) {
        elem.style.zIndex = '';
      }
    }

    return () => {
      if (elem && !isDragging && !isResizing) {
        elem.style.zIndex = '';
      }
    };
  }, [isDragging, isResizing, blockRef]);

  return (
    <div role="button" styleName={`entry ${type === 'break' ? 'break' : ''}`} style={style}>
      <div
        styleName="drag-handle"
        ref={setNodeRef}
        {...listeners}
        onClick={e => {
          e.stopPropagation();
          dispatch(actions.selectEntry(id));
        }}
      >
        <EntryTitle
          title={title}
          duration={duration}
          timeRange={timeRange}
          isBreak={type === 'break'}
        />
      </div>
      <ResizeHandle
        duration={duration}
        maxDuration={parentEndDt ? moment(parentEndDt).diff(startDt, 'minutes') : undefined}
        resizeStartRef={resizeStartRef}
        setLocalDuration={setDuration}
        setGlobalDuration={_setDuration}
        setIsResizing={setIsResizing}
      />
    </div>
  );
}

function EntryTitle({
  title,
  duration,
  timeRange,
  isBreak = false,
}: {
  title: string;
  duration: number;
  timeRange: string;
  isBreak: boolean;
}) {
  const icon = isBreak ? <Icon name="coffee" style={{marginRight: 10}} /> : null;

  if (duration <= 12) {
    return <TinyTitle title={title} timeRange={timeRange} icon={icon} />;
  } else if (duration <= 20) {
    return <SmallTitle title={title} timeRange={timeRange} icon={icon} />;
  }
  return <LongTitle title={title} timeRange={timeRange} icon={icon} duration={duration} />;
}

function TinyTitle({
  title,
  timeRange,
  icon,
}: {
  title: string;
  timeRange: string;
  icon: React.ReactNode | null;
}) {
  return (
    <div styleName="title-wrapper tiny">
      {icon}
      <span styleName="title">{title}</span>, {timeRange}
    </div>
  );
}

function SmallTitle({
  title,
  timeRange,
  icon,
}: {
  title: string;
  timeRange: string;
  icon: React.ReactNode | null;
}) {
  return (
    <div styleName="title-wrapper small">
      {icon}
      <span styleName="title">{title}</span>, {timeRange}
    </div>
  );
}

function LongTitle({
  title,
  timeRange,
  icon,
  duration,
}: {
  title: string;
  timeRange: string;
  icon: React.ReactNode | null;
  duration: number;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [lines, setLines] = useState<number>(1);

  useEffect(() => {
    if (!ref.current) {
      return;
    }
    const lineHeight = parseInt(getComputedStyle(ref.current).lineHeight, 10);
    setLines(Math.floor((minutesToPixels(duration - 2) - 8) / lineHeight) - 1);
  }, [duration]);

  return (
    <div
      ref={ref}
      styleName="title-wrapper long"
      style={{
        padding: '4px 8px',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div styleName="multiline-ellipsis" style={{lineClamp: lines, WebkitLineClamp: lines}}>
        {icon}
        <span styleName="title">{title}</span>
      </div>
      <div>{timeRange}</div>
    </div>
  );
}
