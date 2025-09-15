// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useRef, useState, useMemo} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon, SemanticICONS} from 'semantic-ui-react';

import * as actions from './actions';
import {useDraggable, useDroppable} from './dnd';
import {EntryPopup} from './EntryPopup';
import {formatTimeRange} from './i18n';
import {getWidthAndOffset} from './layout';
import {ReduxState} from './reducers';
import ResizeHandle from './ResizeHandle';
import * as selectors from './selectors';
import {ContribEntry, BreakEntry, EntryType, BlockEntry} from './types';
import {minutesToPixels, pixelsToMinutes, snapPixels, snapMinutes, formatBlockTitle} from './utils';

import './DayTimetable.module.scss';
import './ContributionEntry.module.scss';
import { ENTRY_COLORS_BY_BACKGROUND } from './colors';

interface DraggableEntryProps {
  id: number;
  [key: string]: any;
}

export function DraggableEntry({id, ...rest}: DraggableEntryProps) {
  const dispatch = useDispatch();
  const {
    listeners: _listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: `${id}`,
  });
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );
  // Used to determine whether the entry was just clicked or actually dragged
  // if dragged, this prevents selecting the entry on drag end (and thus showing the popup)
  const isClick = useRef<boolean>(true);

  function onClick(e) {
    e.stopPropagation();
    if (isClick.current) {
      dispatch(actions.selectEntry(id));
    }
  }

  function onMouseDown() {
    isClick.current = true;
  }

  const listeners = {
    ..._listeners,
    onClick,
    onMouseDown: (event: MouseEvent) => {
      if (event.button !== 0) {
        return;
      }

      onMouseDown();
      _listeners.onMouseDown(event);
    },
  };

  useEffect(() => {
    if (isDragging) {
      isClick.current = false;
      dispatch(actions.deselectEntry());
    }
  }, [dispatch, isDragging]);

  const entry = (
    <ContributionEntry
      id={id}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      transform={transform}
      isDragging={isDragging}
    />
  );

  if (isSelected && !isDragging) {
    return (
      <EntryPopup
        trigger={entry}
        onClose={() => {
          dispatch(actions.deselectEntry());
        }}
        entry={{id, ...rest}}
      />
    );
  }

  return entry;
}

export function DraggableBlockEntry({id, ...rest}: DraggableEntryProps) {
  return <DraggableEntry id={id} {...rest} />;
}

interface _DraggableEntryProps {
  selected: boolean;
  setDuration: (duration: number) => void;
  parentEndDt?: moment.Moment;
}

type DraggableContribEntryProps = _DraggableEntryProps & (ContribEntry | BreakEntry | BlockEntry);

export default function ContributionEntry({
  type,
  id,
  startDt,
  duration: _duration,
  title,
  blockRef,
  sessionTitle,
  colors,
  selected,
  y,
  listeners,
  setNodeRef,
  transform,
  isDragging,
  column,
  maxColumn,
  parent,
  setDuration: _setDuration,
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  onMouseUp: _onMouseUp = () => {},
  parentEndDt,
  children: _children = [],
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  setChildDuration = () => {},
  renderChildren = true,
}: DraggableContribEntryProps) {
  const {width, offset} = getWidthAndOffset(column, maxColumn);
  const resizeStartRef = useRef<number | null>(null);
  const [isResizing, setIsResizing] = useState(false);
  const [duration, setDuration] = useState(_duration);
  const {setNodeRef: setDroppableNodeRef} = useDroppable({
    id: `${id}`,
    // disabled: true,
  });
  let style: Record<string, string | number | undefined> = transform
    ? {
        transform: `translate3d(${transform.x}px, ${snapPixels(transform.y)}px, 10px)`,
        // zIndex: 70,
      }
    : {};
  renderChildren = renderChildren && _children.length > 0;

  const styleColors = parent ? ENTRY_COLORS_BY_BACKGROUND[parent.colors.backgroundColor] : colors;

  style = {
    ...style,
    position: 'absolute',
    top: y,
    left: offset,
    width: `calc(${width} - 6px)`,
    height: minutesToPixels(Math.max(duration, minutesToPixels(5)) - 1),
    textAlign: 'left',
    zIndex: isDragging || isResizing ? 1000 : selected ? 80 : style.zIndex,
    cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
    filter: selected ? 'drop-shadow(0 0 2px #000)' : undefined,
    ...styleColors,
  };

  const deltaMinutes = snapMinutes(pixelsToMinutes(transform ? transform.y : 0));
  const newStart = moment(startDt).add(deltaMinutes, 'minutes');
  const newEnd = moment(startDt).add(deltaMinutes + duration, 'minutes');

  const timeRange = formatTimeRange('en', newStart, newEnd); // TODO: use current locale
  // shift children startDt by deltaMinutes
  const children = _children.map(child => ({
    ...child,
    startDt: moment(child.startDt).add(deltaMinutes, 'minutes').format(),
  }));

  // const makeSetDuration = (id: number) => (d: number) => setChildDuration(id, d);
  // const setChildDuration = useCallback(() => {}, [])

  const latestChildEndDt = children.reduce((acc, child) => {
    const endDt = moment(child.startDt).add(child.duration, 'minutes');
    return endDt.isAfter(acc) ? endDt : acc;
  }, moment(startDt));

  useEffect(() => {
    setDuration(_duration);
  }, [_duration]);

  // TODO: (Ajob) Check if this code is necessary
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
      styleName={`entry ${id === 'draft' ? 'draft' : ''} ${renderChildren ? '' : 'simple'}`}
      style={style}
      onMouseUp={() => {
        if (isResizing || isDragging) {
          return;
        }

        _onMouseUp();
      }}
    >
      <div
        styleName="drag-handle"
        style={{
          cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
          display: 'flex',
          padding: 0,
        }}
        ref={setNodeRef}
        {...listeners}
      >
        {/* TODO: (Ajob) Evaluate need for formatBlockTitle */}
        <EntryTitle
          title={type === EntryType.SessionBlock ? formatBlockTitle(sessionTitle, title) : title}
          duration={duration}
          timeRange={timeRange}
          type={type}
        />
        {type === EntryType.SessionBlock && (
          <div
            ref={setDroppableNodeRef}
            style={{
              flexGrow: 1,
              position: 'relative',
              borderRadius: 6,
            }}
          >
            {children.length
              ? children.map(child => (
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
                ))
              : null}
          </div>
        )}
      </div>
      <ResizeHandle
        duration={duration}
        minDuration={latestChildEndDt.diff(startDt, 'minutes')}
        maxDuration={parentEndDt ? moment(parentEndDt).diff(startDt, 'minutes') : undefined}
        resizeStartRef={resizeStartRef}
        setLocalDuration={setDuration}
        setGlobalDuration={_setDuration}
        setIsResizing={setIsResizing}
      />
    </div>
  );
}

export function EntryTitle({
  title,
  duration,
  timeRange,
  type,
}: {
  title: string;
  duration: number;
  timeRange: string;
  type: EntryType;
}) {
  const iconName = {
    [EntryType.Break]: 'coffee',
    [EntryType.Contribution]: 'file alternate outline',
    [EntryType.SessionBlock]: 'calendar alternate outline',
  }[type] as SemanticICONS;

  const icon = iconName ? <Icon name={iconName} style={{marginRight: 10}} /> : null;

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
      <div styleName="time">{timeRange}</div>
    </div>
  );
}
