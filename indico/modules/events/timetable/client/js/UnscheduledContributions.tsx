// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {partition} from 'lodash';
import {Moment} from 'moment';
import React, {useEffect, useRef, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, Input, Dropdown, Icon, Popup} from 'semantic-ui-react';

import {SessionIcon} from 'indico/modules/events/timetable/SessionIcon';
import PopoverDropdownMenu from 'indico/react/components/PopoverDropdownMenu';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import TimetableConfirmDialog from './ConfirmDialog';
import {mapDataToEntry} from './mapperUtils';
import {
  SESSION_CREATE_MODAL,
  SESSION_EDIT_MODAL,
  UNSCHEDULED_CONTRIB_CREATE_MODAL,
  useModal,
} from './ModalContext';
import * as selectors from './selectors';
import './UnscheduledContributions.module.scss';
import {EntryType, UnscheduledContribEntry} from './types';
import {DraggableUnscheduledContributionEntry} from './UnscheduledContributionEntry';

enum GenericFilterType {
  NO_SESSION = 'no-session',
}

type FilterType = GenericFilterType | number;

function UnscheduledContributionList({
  dt,
  contribs,
}: {
  dt: Moment;
  contribs: UnscheduledContribEntry[];
}) {
  const uniqueContribs = [...new Map(contribs.map(contrib => [contrib.id, contrib])).values()];
  return (
    <div styleName="contributions-list">
      {uniqueContribs.map(contrib => (
        <DraggableUnscheduledContributionEntry
          key={contrib.id}
          dt={dt}
          id={contrib.id}
          objId={contrib.objId}
          title={contrib.title}
          duration={contrib.duration}
          sessionId={contrib.sessionId}
        />
      ))}
    </div>
  );
}

export default function UnscheduledContributions({dt}: {dt: Moment}) {
  const dispatch = useDispatch<any>();
  const {openModal} = useModal();
  const minSidebarWidthPx = 320;
  const eventId = useSelector(selectors.getEventId);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const resizing = useRef(false);
  const initialPosition = useRef<number>(0);

  const [selectedFilter, setSelectedFilters] = useState<FilterType[]>([]);
  const [draftSearchQuery, setDraftSearchQuery] = useState('');
  const [filterOpen, setFilterOpen] = useState(false);
  const [filterSearchQuery, setFilterSearchQuery] = useState('');
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);

  const contribs = useSelector(selectors.getUnscheduled).toSorted((c1, c2) => {
    // sort by sessionId then by title
    const c1SessionId = c1.sessionId ?? Number.MAX_SAFE_INTEGER;
    const c2SessionId = c2.sessionId ?? Number.MAX_SAFE_INTEGER;
    if (c1SessionId !== c2SessionId) {
      return c1SessionId - c2SessionId;
    }
    return c1.title.localeCompare(c2.title);
  });
  const sessions = useSelector(selectors.getSessions);
  const prevSessions = useRef(sessions);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const showSessions = useSelector(selectors.showSessions);

  const contribsGrouped = Object.groupBy(contribs, ({sessionId}) => sessionId ?? 'no-session');

  const currentContribs =
    selectedFilter.length > 0
      ? selectedFilter.flatMap(filter => contribsGrouped[filter] ?? [])
      : contribs;
  const filteredContribs = currentContribs.filter(contrib =>
    contrib.title.toLowerCase().includes(draftSearchQuery.toLowerCase())
  );

  const [sessionsWithContribs, sessionsWithoutContribs] = partition(
    Object.values(sessions)
      .map(session => ({
        value: session.id,
        title: session.title,
        color: session.colors,
        count: (contribsGrouped[session.id] ?? []).length,
        text: (
          <div styleName="session">
            <SessionIcon colors={session.colors} />
            <span>{session.title}</span>
          </div>
        ),
      }))
      .toSorted((o1, o2) => o1.title.localeCompare(o2.title)),
    e => e.count > 0
  );

  const dropdownSessions = [
    {
      value: 'no-session',
      title: Translate.string('No assigned session'),
      text: (
        <div styleName="session">
          <SessionIcon />
          <span>
            <Translate>No assigned session</Translate>
          </span>
        </div>
      ),
    },
    ...sessionsWithContribs,
    ...sessionsWithoutContribs,
  ];

  function onMouseUp() {
    resizing.current = false;
    initialPosition.current = 0;
  }

  function onMouseMove(e: MouseEvent) {
    if (!resizing.current || !wrapperRef.current) {
      return;
    }

    const diff = e.pageX - initialPosition.current;
    const width = Math.max(wrapperRef.current.offsetWidth + diff, minSidebarWidthPx);
    wrapperRef.current.style.width = `${width}px`;
    initialPosition.current = wrapperRef.current.getBoundingClientRect().left + width;
  }

  useEffect(() => {
    if (showUnscheduled) {
      setSelectedFilters([]);
      setDraftSearchQuery('');
      setFilterSearchQuery('');
      setFilterOpen(false);
    }
  }, [showUnscheduled]);

  useEffect(() => {
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mousemove', onMouseMove);

    return () => {
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  // Keep track of sessions changes to update filter if needed
  useEffect(() => {
    const oldKeys = Object.keys(prevSessions.current);
    const newKeys = Object.keys(sessions);

    if (!(prevSessions.current && sessions) || oldKeys?.length === newKeys?.length) {
      return;
    }

    let newFilter = null;
    if (oldKeys.length < newKeys.length) {
      newFilter = +newKeys.filter(k => !prevSessions.current[k])?.pop();
    }

    setSelectedFilters(newFilter ? [newFilter] : []);
    prevSessions.current = sessions;
  }, [sessions]);

  // TODO: (Ajob) Once we move to an approach where we have all kinds of draft blocks
  //              I propose we have some kind of filter option to search by entry type,
  //              session, etc. If no filters are applied, everything is visible.
  const [sessionSearchQuery, setSessionSearchQuery] = useState('');

  const filteredSessions = Object.values(sessions)
    .filter(session => session.title.toLowerCase().includes(sessionSearchQuery.toLowerCase()))
    .toSorted((a, b) => a.title.localeCompare(b.title));

  if (!showUnscheduled && !showSessions) {
    return null;
  }
  const filteredDropdownSessions = dropdownSessions.filter(session =>
    session.title.toLowerCase().includes(filterSearchQuery.toLowerCase())
  );
  return (
    <>
      <div styleName="container" style={{minWidth: `${minSidebarWidthPx}px`}} ref={wrapperRef}>
        {showUnscheduled && (
          <>
            <div styleName="container-header">
              <h1 styleName="title">
                <Translate>Unscheduled Contributions</Translate>
              </h1>
              <div styleName="actions">
                <Input
                  icon={
                    draftSearchQuery ? (
                      <Icon name="close" link onClick={() => setDraftSearchQuery('')} />
                    ) : (
                      'search'
                    )
                  }
                  placeholder={Translate.string('Search unscheduled contributions')}
                  value={draftSearchQuery}
                  onChange={(_, {value}) => setDraftSearchQuery(value)}
                />
                <div styleName="filter-trigger-wrapper">
                  <PopoverDropdownMenu
                    open={filterOpen}
                    onOpen={() => setFilterOpen(true)}
                    onClose={() => {
                      setFilterOpen(false);
                      setFilterSearchQuery('');
                    }}
                    overflow
                    trigger={
                      <Button
                        basic
                        type="button"
                        icon="filter"
                        title={Translate.string('Filter by session')}
                      />
                    }
                    searchValue={filterSearchQuery}
                    onSearchChange={setFilterSearchQuery}
                    searchPlaceholder={Translate.string('Search sessions')}
                  >
                    {filteredDropdownSessions.map(option => {
                      const isSelected = selectedFilter.includes(option.value as FilterType);

                      return (
                        <Dropdown.Item
                          key={option.value}
                          active={isSelected}
                          selected={isSelected}
                          onClick={e => {
                            e.stopPropagation();

                            setSelectedFilters(prev =>
                              isSelected
                                ? prev.filter(value => value !== option.value)
                                : [...prev, option.value as FilterType]
                            );
                          }}
                        >
                          {option.text}
                        </Dropdown.Item>
                      );
                    })}
                  </PopoverDropdownMenu>

                  {selectedFilter.length > 0 && (
                    <button
                      type="button"
                      styleName="filter-badge"
                      onClick={e => {
                        e.stopPropagation();
                        setSelectedFilters([]);
                      }}
                    >
                      <span styleName="filter-count">
                        {selectedFilter.length > 9 ? '' : selectedFilter.length}
                      </span>
                      <span styleName="filter-cross">
                        <Icon name="close" />
                      </span>
                    </button>
                  )}
                </div>
              </div>
            </div>
            <div styleName="content">
              <div styleName="gradient" />
              <Button
                styleName="add-element"
                basic
                type="button"
                title={Translate.string('Create new contribution')}
                icon="plus"
                size="small"
                onClick={() =>
                  openModal(UNSCHEDULED_CONTRIB_CREATE_MODAL, {
                    eventId,
                    onCreate: contrib => {
                      // TODO: (Ajob) Instead of manual conversion we should
                      //              adjust the actual endpoint and its usages
                      contrib = mapDataToEntry({...contrib, type: EntryType.Contribution});
                      dispatch(actions.addUnscheduledContrib(contrib));
                      setSelectedFilters([]);
                      setDraftSearchQuery('');
                    },
                  })
                }
              />
              {filteredContribs.length > 0 ? (
                <UnscheduledContributionList dt={dt} contribs={filteredContribs} />
              ) : (
                <div styleName="empty-state">
                  <Icon name="calendar times outline" />
                  <div styleName="empty-state-text">
                    <Translate>No contributions found</Translate>
                  </div>
                </div>
              )}
              <div styleName="gradient" />
            </div>
          </>
        )}

        {showSessions && (
          <>
            <div styleName="container-header">
              <h1 styleName="title">
                <Translate>Sessions</Translate>

                <Popup inverted position="bottom right" basic trigger={<Icon name="info circle" />}>
                  <Translate>
                    Sessions help organize related contributions. When you add a session block to
                    the timetable, you can assign it a session. Contributions placed inside that
                    block automatically inherit the session's location and color, keeping everything
                    consistent.
                  </Translate>
                </Popup>
              </h1>
              <div styleName="actions">
                <Input
                  icon={
                    sessionSearchQuery ? (
                      <Icon name="close" link onClick={() => setSessionSearchQuery('')} />
                    ) : (
                      'search'
                    )
                  }
                  placeholder={Translate.string('Search sessions')}
                  value={sessionSearchQuery}
                  onChange={(_, {value}) => setSessionSearchQuery(value)}
                />
              </div>
            </div>
            <div styleName="content">
              <div styleName="gradient" />
              <Button
                styleName="add-element"
                basic
                type="button"
                title={Translate.string('Create new session')}
                icon="plus"
                size="small"
                onClick={() => openModal(SESSION_CREATE_MODAL, {})}
              />
              {filteredSessions.length > 0 ? (
                <div styleName="session-list">
                  {filteredSessions.map(session => (
                    <div key={session.id} styleName="session-wrapper">
                      <div
                        styleName="session-content"
                        style={
                          {'--session-color': session.colors.backgroundColor} as React.CSSProperties
                        }
                      >
                        <div styleName="session-title">{session.title}</div>
                        <div styleName="session-actions">
                          <Button
                            basic
                            type="button"
                            title={Translate.string('Edit session')}
                            icon="edit"
                            size="small"
                            onClick={() => openModal(SESSION_EDIT_MODAL, {sessionId: session.id})}
                          />
                          <Button
                            basic
                            type="button"
                            title={Translate.string('Delete selected session')}
                            icon="trash"
                            size="small"
                            onClick={() => setSessionToDelete(session.id)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div styleName="empty-state">
                  <Icon name="calendar times outline" />
                  <div styleName="empty-state-text">
                    <Translate>No sessions found</Translate>
                  </div>
                </div>
              )}
              <div styleName="gradient" />
            </div>
          </>
        )}
      </div>
      <div
        styleName="pane-resize-handle"
        onMouseDown={e => {
          if (e.button !== 0) {
            return;
          }
          resizing.current = true;
          initialPosition.current = e.pageX;
        }}
      />
      {sessionToDelete && (
        <TimetableConfirmDialog
          title="Delete session"
          message={
            <Translate>
              Deleting this session will result in unscheduling contibutions associated to it.
            </Translate>
          }
          confirmLabel={Translate.string('Proceed')}
          cancelLabel={Translate.string('Cancel')}
          onClose={() => setSessionToDelete(null)}
          onConfirm={() => {
            dispatch(actions.deleteSession(sessionToDelete));
            setSessionToDelete(null);
          }}
        />
      )}
    </>
  );
}
