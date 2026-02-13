// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React, {useEffect, useRef, useState, useMemo} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Icon} from 'semantic-ui-react';

import * as actions from './actions';
import {ENTRY_COLORS_BY_BACKGROUND} from './colors';
import {useDraggable, useDroppable} from './dnd';
import {EntryMoveButtons} from './EntryMoveButtons';
import {EntryPopup} from './EntryPopup';
import {formatTimeRange} from './i18n';
import {getWidthAndOffset} from './layout';
import ResizeHandle from './ResizeHandle';
import * as selectors from './selectors';
import {ReduxState, ContribEntry, EntryType, BlockEntry, BaseEntry, ScheduledMixin} from './types';
import {
  minutesToPixels,
  pixelsToMinutes,
  snapPixels,
  snapMinutes,
  formatBlockTitle,
  getIconByEntryType,
} from './utils';

import './DayTimetable.module.scss';
import './Entry.module.scss';

interface DraggableEntryProps extends BaseEntry, ScheduledMixin {
  id: string;
  blockRef?: React.RefObject<HTMLDivElement>;
  parentEndDt?: string;
  setDuration: (duration: number) => void;
  setChildDuration?: (id: string) => (duration: number) => void;
}

export function DraggableEntry({id, setDuration, ...rest}: DraggableEntryProps) {
  const dispatch = useDispatch();
  const {listeners: _listeners, setNodeRef, transform, isDragging} = useDraggable({id});
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );
  // Used to determine whether the entry was just clicked or actually dragged
  // if dragged, this prevents selecting the entry on drag end (and thus showing the popup)
  const isClick = useRef<boolean>(true);

  function onClick(evt: React.MouseEvent<HTMLElement>) {
    evt.stopPropagation();
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
    onMouseDown: (event: React.MouseEvent<HTMLElement>) => {
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
      selected={isSelected}
      setDuration={setDuration}
    />
  );

  return (
    <EntryPopup
      trigger={entry}
      open={isSelected}
      onClose={() => {
        dispatch(actions.deselectEntry());
      }}
      // @ts-expect-error The popup will be rewritten soon so let's just ignore this for now
      entry={{id, ...rest}}
    />
  );
}

interface _EntryProps {
  sessionTitle?: string;
  isDragging: boolean;
  transform: {x: number; y: number} | undefined;
  listeners: Record<string, unknown>;
  setNodeRef: (element: HTMLElement | null) => void;
  blockRef?: React.RefObject<HTMLDivElement>;
  selected: boolean;
  setDuration: (duration: number) => void;
  onMouseUp?: () => void;
  setChildDuration?: (id: string) => (duration: number) => void;
  children?: ContribEntry[];
  parent?: BlockEntry | null;
  parentEndDt?: string;
}

type DraggableContribEntryProps = _EntryProps & ScheduledMixin & BaseEntry;

// TODO: (Ajob) Fix these type errors
export default function ContributionEntry({
  type,
  id,
  startDt,
  duration: _duration,
  title,
  blockRef,
  sessionTitle,
  selected,
  y,
  listeners,
  setNodeRef,
  transform,
  isDragging,
  column,
  maxColumn,
  setDuration: _setDuration,
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  onMouseUp: _onMouseUp = () => {},
  // TODO: (Ajob) Check if we can get rid of parentEndDt now that we pass the parent already
  parentEndDt,
  parent,
  colors,
  children: _children = [],
  // eslint-disable-next-line @typescript-eslint/no-shadow, @typescript-eslint/no-unused-vars, @typescript-eslint/no-empty-function
  setChildDuration = (_: string) => (_: number) => {},
}: DraggableContribEntryProps) {
  const {width, offset} = getWidthAndOffset(column, maxColumn);
  const resizeStartRef = useRef<number | null>(null);
  const [isResizing, setIsResizing] = useState(false);
  const [duration, setDuration] = useState(_duration);
  const {setNodeRef: setDroppableNodeRef} = useDroppable({id});

  let style: Record<string, string | number | undefined> = transform
    ? {
        transform: `translate3d(${transform.x}px, ${snapPixels(transform.y)}px, 10px)`,
        // zIndex: 70,
      }
    : {};

  const styleColors = parent ? ENTRY_COLORS_BY_BACKGROUND[parent.colors.backgroundColor] : colors;
  const minHeight = minutesToPixels(5);
  const height = minutesToPixels(Math.max(duration, minHeight)) - 1;

  style = {
    ...style,
    position: 'absolute',
    top: y,
    left: offset,
    width: `calc(${width} - 5px)`,
    height,
    textAlign: 'left',
    zIndex: isDragging || isResizing ? 1000 : selected ? 1 : style.zIndex,
    cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
    boxShadow: selected || isDragging ? `0 0 0 4px rgba(0,0,0,0.1)` : undefined,
    ...styleColors,
  };

  const deltaMinutes = snapMinutes(pixelsToMinutes(transform ? transform.y : 0));
  const newStart = moment(startDt).add(deltaMinutes, 'minutes');
  const newEnd = moment(startDt).add(deltaMinutes + duration, 'minutes');

  const timeRange = formatTimeRange('en', newStart, newEnd); // TODO: use current locale
  // shift children startDt by deltaMinutes
  const children: ContribEntry[] = _children.map(child => ({
    ...child,
    startDt: moment(child.startDt).add(deltaMinutes, 'minutes'),
  }));

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
        elem.style.zIndex = '1000';
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

  const btnColors = {backgroundColor: styleColors.color, color: styleColors.backgroundColor};

  return (
    <div
      role="button"
      styleName="entry"
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
          borderLeftColor: selected || isDragging ? `${colors.color}66` : `${styleColors.color}33`,
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
            styleName="children-wrapper"
            style={{
              backgroundImage: `radial-gradient(${colors.color}11 1px, transparent 0)`,
              backgroundColor: `${colors.color}11`,
            }}
          >
            {children.map(child => (
              <DraggableEntry
                key={child.id}
                setDuration={_children ? setChildDurations[child.id] : null}
                blockRef={blockRef}
                parentEndDt={moment(startDt)
                  .add(deltaMinutes + duration, 'minutes')
                  .format()}
                {...child}
              />
            ))}
          </div>
        )}
      </div>
      <EntryMoveButtons
        id={id}
        sessionBlockId={parent?.id}
        startDt={startDt}
        duration={duration}
        colors={btnColors}
      />
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
  timeRange,
  type,
  duration,
}: {
  title: string;
  timeRange: string;
  type: EntryType;
  duration?: number;
}) {
  const ref = useRef<HTMLDivElement | null>(null);
  const [lines, setLines] = useState<number>(1);

  useEffect(() => {
    if (!ref.current || !duration) {
      return;
    }
    const lineHeight = parseInt(getComputedStyle(ref.current).lineHeight, 10);
    setLines(Math.floor((minutesToPixels(duration - 1) - 9) / lineHeight) - 2);
  }, [duration]);

  return (
    <div
      ref={ref}
      styleName="title-wrapper"
      style={{
        lineClamp: lines,
        WebkitLineClamp: lines,
      }}
    >
      <div styleName="title-overflow-wrapper">
        <Icon name={getIconByEntryType(type)} />
        <span
          styleName="title"
          style={{
            lineClamp: lines,
            WebkitLineClamp: lines,
          }}
        >
          {title}
        </span>
      </div>
      <span styleName="time">{timeRange}</span>
    </div>
  );
}
