// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {partition} from 'lodash';
import {Moment} from 'moment';
import React, {Fragment, ReactNode, useEffect, useMemo, useRef, useState} from 'react';
import {useSelector} from 'react-redux';
import {Button, DropdownHeader, DropdownItemProps, Label, Select} from 'semantic-ui-react';

import SessionEditForm, {SessionCreateForm} from 'indico/modules/events/sessions/SessionForm';
import {Translate} from 'indico/react/i18n';

import * as selectors from './selectors';
import './UnscheduledContributions.module.scss';
import {DraggableUnscheduledContributionEntry} from './UnscheduledContributionEntry';

enum FilterType {
  ALL = 'all-sessions',
  NO_SESSION = 'no-session',
}

function FragmentWithoutWarning({key, children}: {key: string; children: ReactNode}) {
  return <Fragment key={key}>{children}</Fragment>;
}

function UnscheduledContributionList({dt, contribs}: {dt: Moment; contribs: any[]}) {
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: '1em'}}>
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
  const eventId = useSelector(selectors.getEventId);
  const eventType = useSelector(selectors.getEventType);
  const contribs = useSelector(selectors.getUnscheduled);
  const contribsGrouped = Object.groupBy(contribs, ({sessionId}) => sessionId ?? 'no-session');
  const sessions = useSelector(selectors.getSessions);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const wrapperRef = useRef(null);
  const minSidebarWidthPx = 280;

  const [selectedFilter, setSelectedFilter] = useState<string | FilterType>('no-session');
  const [draftSessionId, setDraftSessionId] = useState<number | 'new' | null>(null);

  const resizing = useRef<boolean>(false);
  const initialPosition = useRef<number>(0);

  useEffect(() => {
    function onMouseUp() {
      resizing.current = false;
      initialPosition.current = 0;
    }

    function onMouseMove(e) {
      if (resizing.current) {
        const diff = e.pageX - initialPosition.current;
        const width = wrapperRef.current.offsetWidth + diff;
        if (width >= minSidebarWidthPx) {
          initialPosition.current = e.pageX;
          wrapperRef.current.style.width = `${width}px`;
        }
      }
    }

    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mousemove', onMouseMove);
    return () => {
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  const sessionSearch = (options: DropdownItemProps[], value: string) =>
    options.filter(o => o.title && o.title.toLowerCase().includes(value.toLowerCase()));

  const currentContribs = useMemo(() => {
    return selectedFilter ? (contribsGrouped[selectedFilter] ?? []) : contribs;
  }, [contribs, selectedFilter, contribsGrouped]);

  const [sessionsWithContribs, sessionsWithoutContribs] = partition(
    Object.entries(sessions)
      .map(([id, session]) => ({
        value: +id,
        title: session.title,
        count: (contribsGrouped[id] ?? []).length,
        text: (
          <div styleName="session">
            <Label empty circular style={{...session.colors}} />
            {session.title}
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
          <Translate>No assigned session</Translate>
        </div>
      ),
    },
    {
      as: FragmentWithoutWarning,
      key: 'sep-with-contribs',
      content: (
        <DropdownHeader>
          <Translate>Sessions with contributions</Translate>
        </DropdownHeader>
      ),
    },
    ...sessionsWithContribs,
    {
      as: FragmentWithoutWarning,
      key: 'sep-without-contribs',
      content: (
        <DropdownHeader>
          <Translate>Empty sessions</Translate>
        </DropdownHeader>
      ),
    },
    ...sessionsWithoutContribs,
  ];

  if (!showUnscheduled) {
    return null;
  }

  // TODO: (Ajob) Once we move to an approach where we have all kinds of draft blocks
  //              I propose we have some kind of filter option to search by entry type,
  //              session, etc. If no filters are applied, everything is visible.
  return (
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
              placeholder={Translate.string('All sessions')}
              search={sessionSearch}
              onClose={() => {
                const searchInput = wrapperRef.current.querySelector(
                  'div .ui.button.search.selection.dropdown input.search'
                );
                searchInput.blur();
              }}
              noResultsMessage={Translate.string('No sessions found.')}
              clearable
              defaultValue="no-session"
              onChange={(_, {value}: {_: unknown; value: string}) => setSelectedFilter(value)}
              options={dropdownSessions}
            />
            {Number.isInteger(selectedFilter) && (
              <Button
                basic
                type="button"
                title={Translate.string('Edit selected session')}
                icon="edit"
                size="small"
                disabled={!Number.isInteger(+selectedFilter)}
                onClick={() => setDraftSessionId(+selectedFilter)}
              />
            )}
            <Button
              basic
              type="button"
              title={Translate.string('Create new session')}
              icon="plus"
              size="small"
              onClick={() => setDraftSessionId('new')}
            />
          </div>
          {draftSessionId === 'new' && (
            <SessionCreateForm
              eventId={eventId}
              eventType={eventType}
              onClose={() => setDraftSessionId(null)}
            />
          )}
          {Number.isInteger(draftSessionId) && (
            <SessionEditForm
              eventId={eventId}
              eventType={eventType}
              sessionId={draftSessionId as number}
              onClose={() => setDraftSessionId(null)}
            />
          )}
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
    </>
  );
}
