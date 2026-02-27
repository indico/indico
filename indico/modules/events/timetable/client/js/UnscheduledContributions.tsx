// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {partition} from 'lodash';
import {Moment} from 'moment';
import React, {Fragment, ReactNode, useEffect, useRef, useState} from 'react';
import {useDispatch, useSelector} from 'react-redux';
import {Button, DropdownHeader, DropdownItemProps, Label, Select} from 'semantic-ui-react';

import {SessionIcon} from 'indico/modules/events/timetable/SessionIcon';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';
import './UnscheduledContributions.module.scss';
import {TimetableSessionCreateModal, TimetableSessionEditModal} from './TimetableSessionModal';
import {UnscheduledContribEntry} from './types';
import {DraggableUnscheduledContributionEntry} from './UnscheduledContributionEntry';

enum GenericFilterType {
  NO_SESSION = 'no-session',
}

type FilterType = GenericFilterType & number;

function FragmentWithoutWarning({key, children}: {key: string; children: ReactNode}) {
  return <Fragment key={key}>{children}</Fragment>;
}

function UnscheduledContributionList({
  dt,
  contribs,
}: {
  dt: Moment;
  contribs: UnscheduledContribEntry[];
}) {
  return (
    <div styleName="contributions-list">
      {contribs.map(contrib => (
        <DraggableUnscheduledContributionEntry
          key={contrib.id}
          dt={dt}
          id={contrib.id}
          title={contrib.title}
          duration={contrib.duration}
          colors={contrib.colors}
        />
      ))}
    </div>
  );
}

export default function UnscheduledContributions({dt}: {dt: Moment}) {
  const dispatch = useDispatch<any>();
  const minSidebarWidthPx = 320;

  const wrapperRef = useRef<HTMLDivElement>(null);
  const resizing = useRef(false);
  const initialPosition = useRef<number>(0);

  const [selectedFilter, setSelectedFilter] = useState<FilterType>();
  const [selectedSessionId, setSelectedSessionId] = useState<number | 'draft'>();

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

  const contribsGrouped = Object.groupBy(contribs, ({sessionId}) => sessionId ?? 'no-session');

  const currentContribs = selectedFilter ? (contribsGrouped[selectedFilter] ?? []) : contribs;

  const [sessionsWithContribs, sessionsWithoutContribs] = partition(
    Object.values(sessions)
      .map(session => ({
        value: session.id,
        title: session.title,
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
      as: FragmentWithoutWarning,
      key: 'sep-filters',
      disabled: true,
      content: (
        <DropdownHeader>
          <Translate>Filters</Translate>
        </DropdownHeader>
      ),
    },
    {
      value: 'no-session',
      title: Translate.string('No assigned session'),
      text: (
        <div styleName="session">
          <Label empty circular color="grey" />
          <span>
            <Translate>No assigned session</Translate>
          </span>
        </div>
      ),
    },
    ...(sessionsWithContribs.length
      ? [
          {
            as: FragmentWithoutWarning,
            key: 'sep-with-contribs',
            disabled: true,
            content: (
              <DropdownHeader>
                <Translate>Sessions with contributions</Translate>
              </DropdownHeader>
            ),
          },
        ]
      : []),
    ...sessionsWithContribs,
    ...(sessionsWithoutContribs.length
      ? [
          {
            as: FragmentWithoutWarning,
            key: 'sep-without-contribs',
            disabled: true,
            content: (
              <DropdownHeader>
                <Translate>Empty sessions</Translate>
              </DropdownHeader>
            ),
          },
        ]
      : []),
    ...sessionsWithoutContribs,
  ];

  const sessionSearch = (options: DropdownItemProps[], value: string) =>
    options
      // Primary filter to match search term
      .filter(
        o => o.as === FragmentWithoutWarning || o.title.toLowerCase().includes(value.toLowerCase())
      )
      // Secondary filter to remove consecutive dividers
      .filter(
        (o, i, arr) =>
          o.as !== FragmentWithoutWarning ||
          (arr[i + 1] && arr[i + 1].as !== FragmentWithoutWarning)
      );

  function onMouseUp() {
    resizing.current = false;
    initialPosition.current = 0;
  }

  function onMouseMove(e: MouseEvent) {
    if (resizing.current) {
      const diff = e.pageX - initialPosition.current;
      const width = Math.max(wrapperRef.current.offsetWidth + diff, minSidebarWidthPx);
      initialPosition.current = wrapperRef.current.offsetLeft + width;
      wrapperRef.current.style.width = `${width}px`;
    }
  }

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

    setSelectedFilter(newFilter);
    prevSessions.current = sessions;
  }, [sessions]);

  // TODO: (Ajob) Once we move to an approach where we have all kinds of draft blocks
  //              I propose we have some kind of filter option to search by entry type,
  //              session, etc. If no filters are applied, everything is visible.
  return (
    showUnscheduled && (
      <>
        <div
          styleName="contributions-container"
          style={{minWidth: `${minSidebarWidthPx}px`}}
          ref={wrapperRef}
        >
          <div styleName="content">
            <div styleName="actions">
              <Select
                button
                placeholder={Translate.string('Filter sessions')}
                value={selectedFilter}
                selectOnBlur={false}
                selectOnNavigation={false}
                search={sessionSearch}
                noResultsMessage={Translate.string('No sessions found')}
                clearable
                onChange={(_, {value}: {_: unknown; value: FilterType}) => {
                  // TODO: (Ajob) Fix bug where clicking enter on an option
                  //              keeps dropdown open.
                  setSelectedFilter(value);
                }}
                styleName="session-filter"
                options={dropdownSessions}
              />
              {Number.isInteger(selectedFilter) && (
                <Button
                  basic
                  type="button"
                  title={Translate.string('Edit selected session')}
                  icon="edit"
                  size="small"
                  onClick={() => setSelectedSessionId(selectedFilter)}
                />
              )}
              {Number.isInteger(selectedFilter) && (
                <Button
                  basic
                  type="button"
                  title={Translate.string('Delete selected session')}
                  icon="trash"
                  size="small"
                  onClick={() => {
                    dispatch(actions.deleteSession(selectedFilter));
                  }}
                />
              )}
              <Button
                basic
                type="button"
                title={Translate.string('Create new session')}
                icon="plus"
                size="small"
                onClick={() => setSelectedSessionId('draft')}
              />
            </div>
            {currentContribs.length > 0 ? (
              <UnscheduledContributionList dt={dt} contribs={currentContribs} />
            ) : (
              <Translate>This session has no contributions</Translate>
            )}
          </div>
        </div>
        <div
          styleName="pane-resize-handle"
          onMouseDown={e => {
            resizing.current = true;
            initialPosition.current = e.pageX;
          }}
        />
        {selectedSessionId &&
          (selectedSessionId === 'draft' ? (
            <TimetableSessionCreateModal onClose={() => setSelectedSessionId(null)} />
          ) : (
            <TimetableSessionEditModal
              onClose={() => setSelectedSessionId(null)}
              sessionId={selectedSessionId}
            />
          ))}
      </>
    )
  );
}
