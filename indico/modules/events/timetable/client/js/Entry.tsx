// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment, {Moment} from 'moment';
import React, {useEffect, useRef, useState, useMemo, useCallback} from 'react';
import {useSelector} from 'react-redux';
import {Icon, SemanticICONS} from 'semantic-ui-react';

import {PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

import * as actions from './actions';
import {useDraggable, useDroppable} from './dnd';
import {EntryMoveButtons} from './EntryMoveButtons';
import {EntryPopup} from './EntryPopup';
import {formatTimeRange} from './i18n';
import {getWidthAndOffset} from './layout';
import ResizeHandle from './ResizeHandle';
import * as selectors from './selectors';
import {ReduxState, EntryType, BaseEntry, ScheduledMixin, EntryUniqueID, ChildEntry} from './types';
import {
  minutesToPixels,
  pixelsToMinutes,
  snapMinutes,
  formatBlockTitle,
  getIconByEntryType,
  getEntryColors,
  MIN_DURATION,
  V_SPACE_BETWEEN_ENTRIES_PX,
  useTimetableDispatch,
  getDateKey,
} from './utils';

import './DayTimetable.module.scss';
import './Entry.module.scss';

interface DraggableEntryProps extends BaseEntry, ScheduledMixin {
  id: EntryUniqueID;
  dt: Moment;
  blockRef?: React.RefObject<HTMLDivElement>;
  parentEndDt?: string;
}

export function DraggableEntry({id, dt, ...rest}: DraggableEntryProps) {
  const dispatch = useTimetableDispatch();
  const {listeners: _listeners, setNodeRef, isDragging, ref} = useDraggable({id});
  const isSelected = useSelector((state: ReduxState) =>
    selectors.makeIsSelectedSelector()(state, id)
  );
  const isPosterBlock = useSelector((state: ReduxState) =>
    selectors.isPosterSessionBlock(state, id)
  );
  const eventId = useSelector(selectors.getEventId);
  // Used to determine whether the entry was just clicked or actually dragged
  // if dragged, this prevents selecting the entry on drag end (and thus showing the popup)
  const isClick = useRef<boolean>(true);

  function onClick(evt: React.MouseEvent<HTMLElement>) {
    if (evt.target instanceof Node && !ref.current.contains(evt.target)) {
      return;
    }
    evt.stopPropagation();
    if (isClick.current) {
      dispatch(actions.selectEntry(id));
    }
  }

  function onDoubleClick(evt: React.MouseEvent<HTMLElement>) {
    if (evt.target instanceof Node && !ref.current.contains(evt.target)) {
      return;
    }
    evt.stopPropagation();
    if (rest.type !== EntryType.SessionBlock || isPosterBlock) {
      return;
    }
    dispatch(actions.deselectEntry());
    dispatch(actions.setExpandedSessionBlock(id, eventId));
  }

  function onMouseDown() {
    isClick.current = true;
  }

  const listeners = {
    ..._listeners,
    onClick,
    onDoubleClick,
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
    <Entry
      id={id}
      dt={dt}
      {...rest}
      listeners={listeners}
      setNodeRef={setNodeRef}
      isDragging={isDragging}
      selected={isSelected}
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
  id: EntryUniqueID;
  dt: Moment;
  transform?: {x: number; y: number};
  isDragging?: boolean;
  isPlaceholder?: boolean;
  listeners: Record<string, unknown>;
  setNodeRef: (element: HTMLElement | null) => void;
  blockRef?: React.RefObject<HTMLDivElement>;
  selected: boolean;
  onMouseUp?: () => void;
  children?: ChildEntry[];
  parentEndDt?: string;
  sessionId?: number;
  sessionBlockId?: string;
}

type EntryProps = _EntryProps & ScheduledMixin & BaseEntry;

function DroppableArea({id, horizontalPadding}: {id: string; horizontalPadding?: string}) {
  const {setNodeRef: setDroppableNodeRef, hasDraggableOver} = useDroppable({id});

  return (
    <div styleName={`children-droppable-container ${hasDraggableOver ? 'hovered' : ''}`}>
      <div styleName="children-droppable-outline" style={{padding: `0 ${horizontalPadding}`}}>
        <div ref={setDroppableNodeRef} styleName="children-droppable" />
      </div>
    </div>
  );
}

// TODO: (Ajob) Fix these type errors
export default function Entry({
  type,
  id,
  startDt,
  dt,
  duration: _duration,
  title,
  blockRef,
  selected,
  y,
  listeners,
  setNodeRef,
  transform,
  isDragging = false,
  isPlaceholder = false,
  column,
  maxColumn,
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  onMouseUp: _onMouseUp = () => {},
  // TODO: (Ajob) Check if we can get rid of parentEndDt now that we pass the parent already
  parentEndDt,
  sessionId,
  sessionBlockId,
  colors: customColors,
  children: _children = [],
}: EntryProps) {
  const dispatch = useTimetableDispatch();
  const isPosterBlock = useSelector((state: ReduxState) =>
    selectors.isPosterSessionBlock(state, id)
  );
  const session = useSelector((state: ReduxState) => selectors.getSessionById(state, sessionId));
  const {width, offset} = getWidthAndOffset(column, maxColumn);
  const entryRef = useRef<HTMLDivElement>(null);
  const resizeStartRef = useRef<number | null>(null);
  const [isResizing, setIsResizing] = useState(false);
  const [duration, setTempDuration] = useState(_duration);
  const [droppableArea, setDroppableArea] = useState<'full' | 'partial'>('full');
  const colors = getEntryColors({type, sessionBlockId, colors: customColors}, session);
  const btnColors = {backgroundColor: colors.color, color: colors.backgroundColor};
  const hasDraftEntry = useSelector(selectors.hasDraftEntry);
  const eventEndDt = useSelector(selectors.getEventEndDt);
  const maxDuration = useMemo(() => {
    if (parentEndDt) {
      return moment(parentEndDt).diff(startDt, 'minutes');
    }
    return eventEndDt.diff(startDt, 'minutes');
  }, [parentEndDt, eventEndDt, startDt]);

  const minHeight = minutesToPixels(5);
  const height = minutesToPixels(Math.max(duration, minHeight)) - V_SPACE_BETWEEN_ENTRIES_PX;

  const style = {
    opacity: isDragging && !isPlaceholder ? 0 : 1,
    position: 'absolute',
    top: y,
    left: offset,
    width: `calc(${width} - 5px)`,
    height,
    textAlign: 'left',
    zIndex: isDragging || isResizing ? 1000 : selected ? 1 : 0,
    cursor: isResizing ? undefined : isDragging ? 'grabbing' : 'grab',
    boxShadow: selected || isDragging ? `0 0 0 4px rgba(0,0,0,0.1)` : undefined,
    ...colors,
  };

  const deltaMinutes = snapMinutes(pixelsToMinutes(transform ? transform.y : 0));
  const newStart = moment(startDt).add(deltaMinutes, 'minutes');
  const newEnd = moment(startDt).add(deltaMinutes + duration, 'minutes');

  const locale = moment.locale().replace('_', '-');
  const timeRange = formatTimeRange(locale, newStart, newEnd);
  // shift children startDt by deltaMinutes
  const children = _children.map(child => ({
    ...child,
    startDt: moment(child.startDt).add(deltaMinutes, 'minutes'),
  }));

  const latestChildEndDt = children.reduce((acc, child) => {
    const endDt = moment(child.startDt).add(child.duration, 'minutes');
    return endDt.isAfter(acc) ? endDt : acc;
  }, moment(startDt));

  useEffect(() => {
    setTempDuration(_duration);
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

  useEffect(() => {
    if (type !== EntryType.SessionBlock || !entryRef.current) {
      return;
    }
    function updateDroppableArea(entryWidth: number) {
      if (entryWidth - 5 > 250) {
        setDroppableArea('partial');
      } else {
        setDroppableArea('full');
      }
    }

    const observer = new ResizeObserver(entries => {
      const entryWidth = entries[0].contentRect.width;
      updateDroppableArea(entryWidth);
    });
    observer.observe(entryRef.current);

    updateDroppableArea(entryRef.current.clientWidth);

    return () => observer.disconnect();
  }, [id, type]);

  const commitDuration = useCallback(
    (newDuration: number) => {
      dispatch(actions.resizeEntry(id, newDuration, getDateKey(dt)));
    },
    [id, dt, dispatch]
  );

  return (
    <div
      role="button"
      styleName="entry"
      ref={entryRef}
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
          borderLeftColor: selected || isDragging ? `${colors.color}66` : `${colors.color}33`,
        }}
        ref={setNodeRef}
        {...listeners}
      >
        {/* TODO: (Ajob) Evaluate need for formatBlockTitle */}
        <EntryTitle
          title={
            type === EntryType.SessionBlock ? formatBlockTitle(session?.title ?? '', title) : title
          }
          duration={duration}
          timeRange={timeRange}
          type={type}
          {...(isPosterBlock ? {icon: 'flag outline'} : {})}
        />
        {isPosterBlock && <PosterCount count={children.length} />}
        {type === EntryType.SessionBlock && !isPosterBlock && (
          <div
            styleName="children-wrapper"
            style={{
              backgroundImage: `radial-gradient(${colors.color}11 1px, transparent 0)`,
              backgroundColor: `${colors.color}11`,
            }}
          >
            {children.map(child =>
              isPlaceholder ? (
                <Entry
                  key={child.id}
                  dt={dt}
                  listeners={{}}
                  isPlaceholder
                  selected={false}
                  setNodeRef={() => null}
                  {...child}
                  blockRef={blockRef}
                  parentEndDt={moment(startDt)
                    .add(deltaMinutes + duration, 'minutes')
                    .format()}
                  sessionId={child.sessionId ?? undefined}
                />
              ) : (
                <DraggableEntry
                  key={child.id}
                  dt={dt}
                  blockRef={blockRef}
                  parentEndDt={moment(startDt)
                    .add(deltaMinutes + duration, 'minutes')
                    .format()}
                  {...child}
                />
              )
            )}
            {!isPlaceholder &&
              type === EntryType.SessionBlock &&
              !isPosterBlock &&
              droppableArea === 'partial' && <DroppableArea id={id} />}
          </div>
        )}
      </div>
      {!isPlaceholder &&
        type === EntryType.SessionBlock &&
        !isPosterBlock &&
        droppableArea === 'full' && <DroppableArea id={id} horizontalPadding="15px" />}
      {!hasDraftEntry && !isDragging && (
        <EntryMoveButtons
          id={id}
          sessionBlockId={sessionBlockId}
          startDt={startDt}
          duration={duration}
          colors={btnColors}
        />
      )}
      <ResizeHandle
        duration={duration}
        minDuration={Math.max(MIN_DURATION, latestChildEndDt.diff(startDt, 'minutes'))}
        maxDuration={maxDuration}
        resizeStartRef={resizeStartRef}
        setTempDuration={setTempDuration}
        commitDuration={commitDuration}
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
  icon,
}: {
  title: string;
  timeRange: string;
  type: EntryType;
  duration?: number;
  icon?: SemanticICONS;
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
        <Icon name={icon || getIconByEntryType(type)} />
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

function PosterCount({count}: {count: number}) {
  return (
    <span styleName="poster-count">
      <PluralTranslate count={count}>
        <Singular>
          <Param name="count" value={count} /> poster
        </Singular>
        <Plural>
          <Param name="count" value={count} /> posters
        </Plural>
      </PluralTranslate>
    </span>
  );
}
