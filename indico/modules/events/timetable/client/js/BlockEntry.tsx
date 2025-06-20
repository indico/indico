// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useRef, useState, useMemo} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import * as actions from './actions';
import {useDroppable} from './dnd';
import {DraggableEntry} from './Entry';
import {formatTimeRange} from './i18n';
import {getWidthAndOffset} from './layout';
import ResizeHandle from './ResizeHandle';
import {BlockEntry as _BlockEntry} from './types';
import {minutesToPixels, pixelsToMinutes, snapPixels, snapMinutes, formatBlockTitle} from './utils';

import './DayTimetable.module.scss';
import './BlockEntry.module.scss';

interface _DraggableEntryProps {
  selected: boolean;
  setDuration: (duration: number) => void;
  parentEndDt?: moment.Moment;
}

type DraggableBlockEntryProps = _DraggableEntryProps &
  _BlockEntry & {setChildDuration: (childId: number, duration: number) => void};

export default function BlockEntry({
  id,
  startDt,
  duration: _duration,
  title,
  sessionTitle,
  sessionId,
  conveners,
  selected,
  y,
  column,
  maxColumn,
  children: _children = [],
  setDuration: _setDuration,
  setChildDuration,
  listeners,
  setNodeRef,
  transform,
  isDragging,
  renderChildren = true,
  onMouseUp: _onMouseUp = () => {},
}: DraggableBlockEntryProps) {
  const {width, offset} = getWidthAndOffset(column, maxColumn);
  const dispatch = useDispatch();
  const blockRef = useRef<HTMLDivElement | null>(null);
  const mouseEventRef = useRef<MouseEvent | null>(null);
  const resizeStartRef = useRef(null);
  const [isResizing, setIsResizing] = useState(false);
  const [duration, setDuration] = useState(_duration);
  const sessionData = useSelector(state => state.sessions[sessionId]);
  const {setNodeRef: setDroppableNodeRef} = useDroppable({
    id: `${id}`,
    // disabled: true,
  });
  let style: Record<string, string | number | undefined> = transform
    ? {
        transform: `translate3d(${transform.x}px, ${snapPixels(transform.y)}px, 0)`,
      }
    : {};
  renderChildren = renderChildren && _children.length > 0;

  style = {
    ...style,
    position: 'absolute',
    top: y,
    left: offset,
    width: `calc(${width} - 6px)`,
    height: minutesToPixels(duration - 1),
    textAlign: 'left',
    zIndex: isDragging || isResizing ? 90 : selected ? 80 : style.zIndex,
    filter: selected ? 'drop-shadow(0 0 2px #000)' : undefined,
    containerType: 'inline-size',
    backgroundColor: (sessionData || {}).backgroundColor,
    color: (sessionData || {}).textColor,
    // overflow: 'hidden',
  };

  useEffect(() => {
    function onMouseMove(event: MouseEvent) {
      mouseEventRef.current = event;
    }

    document.addEventListener('mousemove', onMouseMove);
    return () => {
      document.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  const deltaMinutes = snapMinutes(pixelsToMinutes(transform ? transform.y : 0));
  const newStart = moment(startDt).add(deltaMinutes, 'minutes');
  const newEnd = moment(startDt).add(deltaMinutes + duration, 'minutes');

  const timeRange = formatTimeRange('en', newStart, newEnd); // TODO: use current locale
  // shift children startDt by deltaMinutes
  const children = _children.map(child => ({
    ...child,
    startDt: moment(child.startDt)
      .add(deltaMinutes, 'minutes')
      .format(),
  }));

  // const makeSetDuration = (id: number) => (d: number) => setChildDuration(id, d);
  // const setChildDuration = useCallback(() => {}, [])

  const latestChildEndDt = children.reduce((acc, child) => {
    const endDt = moment(child.startDt).add(child.duration, 'minutes');
    return endDt.isAfter(acc) ? endDt : acc;
  }, moment(startDt));

  const setChildDurations = useMemo(() => {
    const obj = {};
    for (const e of _children) {
      obj[e.id] = setChildDuration(e.id);
    }
    return obj;
  }, [_children, setChildDuration]);

  return (
    <div
      role="button"
      styleName={`entry block ${renderChildren ? '' : 'simple'}`}
      style={style}
      ref={blockRef}
      onMouseUp={() => {
        if (isResizing || isDragging) {
          return;
        }

        _onMouseUp();
      }}
    >
      <div
        styleName="drag-handle"
        ref={setNodeRef}
        style={{
          cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
          display: 'flex',
          padding: 0,
        }}
        {...listeners}
      >
        <BlockTitle
          title={formatBlockTitle(sessionTitle, title)}
          duration={duration}
          timeRange={timeRange}
        />
        {renderChildren ? (
          <div
            ref={setDroppableNodeRef}
            style={{
              flexGrow: 1,
              position: 'relative',
              borderRadius: 6,
            }}
          >
            {children.map(child => (
              <DraggableEntry
                key={child.id}
                selected={false}
                setDuration={_children ? setChildDurations[child.id] : null}
                blockRef={blockRef}
                parentEndDt={moment(startDt)
                  .add(deltaMinutes + duration, 'minutes')
                  .format()}
                {...child}
              />
            ))}
          </div>
        ) : null}
      </div>
      {/* TODO cannot resize to be smaller than its contents */}
      <ResizeHandle
        forBlock
        duration={duration}
        minDuration={latestChildEndDt.diff(startDt, 'minutes')}
        resizeStartRef={resizeStartRef}
        setLocalDuration={setDuration}
        setGlobalDuration={_setDuration}
        setIsResizing={setIsResizing}
      />
    </div>
  );
}

function BlockTitle({
  title,
  duration,
  timeRange,
}: {
  title: string;
  duration: number;
  timeRange: string;
}) {
  const icon = <Icon name="calendar alternate outline" style={{marginRight: 10}} />;

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
    setLines(Math.floor((minutesToPixels(duration - 1) - 9) / lineHeight) - 1);
  }, [duration]);

  return (
    <div ref={ref} styleName="title-wrapper long">
      <div styleName="multiline-ellipsis" style={{lineClamp: lines, WebkitLineClamp: lines}}>
        {icon}
        <span styleName="title">{title}</span>
      </div>
      <div styleName="time">{timeRange}</div>
    </div>
  );
}
