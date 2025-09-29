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
import {UnscheduledContrib} from './types';
import {DraggableUnscheduledContributionEntry} from './UnscheduledContributionEntry';

enum GenericFilterType {
  NO_SESSION = 'no-session',
}

type FilterType = GenericFilterType & number;

function FragmentWithoutWarning({key, children}: {key: string; children: ReactNode}) {
  return <Fragment key={key}>{children}</Fragment>;
}

function UnscheduledContributionList({dt, contribs}: {dt: Moment; contribs: UnscheduledContrib[]}) {
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
  const minSidebarWidthPx = 280;

  const wrapperRef = useRef<HTMLDivElement>(null);
  const resizing = useRef(false);
  const initialPosition = useRef<number>(0);

  const [selectedFilter, setSelectedFilter] = useState<FilterType>();
  const [selectedSessionId, setSelectedSessionId] = useState<number | 'draft'>();

  const eventId = useSelector(selectors.getEventId);
  const eventType = useSelector(selectors.getEventType);
  const contribs = useSelector(selectors.getUnscheduled);
  const sessions = useSelector(selectors.getSessions);
  const showUnscheduled = useSelector(selectors.showUnscheduled);

  const contribsGrouped = useMemo(
    () => Object.groupBy(contribs, ({sessionId}) => sessionId ?? 'no-session'),
    [contribs]
  );

  const currentContribs = useMemo(() => {
    return selectedFilter ? (contribsGrouped[selectedFilter] ?? []) : contribs;
  }, [contribs, selectedFilter, contribsGrouped]);

  const [sessionsWithContribs, sessionsWithoutContribs] = useMemo(
    () =>
      partition(
        Object.entries(sessions)
          .map(([id, session]) => ({
            value: id,
            title: session.title,
            count: (contribsGrouped[id] ?? []).length,
            text: (
              <div styleName="session">
                <Label empty circular style={{...session.colors}} />
                <span>{session.title}</span>
              </div>
            ),
          }))
          .toSorted((o1, o2) => o1.title.localeCompare(o2.title)),
        e => e.count > 0
      ),
    [sessions, contribsGrouped]
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
          <span>
            <Translate>No assigned session</Translate>
          </span>
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

  const sessionSearch = (options: DropdownItemProps[], value: string) =>
    options.filter(o => o.title && o.title.toLowerCase().includes(value.toLowerCase()));

  const blurDropdown = () => {
    const searchInput = wrapperRef.current.querySelector<HTMLInputElement>(
      'div .ui.button.search.selection.dropdown input.search'
    );
    searchInput?.blur();
  };

  function onMouseUp() {
    resizing.current = false;
    initialPosition.current = 0;
  }

  function onMouseMove(e: MouseEvent) {
    if (resizing.current) {
      const diff = e.pageX - initialPosition.current;
      const width = wrapperRef.current.offsetWidth + diff;

      if (width >= minSidebarWidthPx) {
        initialPosition.current = e.pageX;
        wrapperRef.current.style.width = `${width}px`;
      }
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
                search={sessionSearch}
                onClose={blurDropdown}
                noResultsMessage={Translate.string('No sessions found')}
                clearable
                onChange={(_, {value}: {_: unknown; value: FilterType}) => {
                  // TODO: (Ajob) Fix bug where clicking enter on an options
                  //              keeps dropdown open.
                  setSelectedFilter(value);
                }}
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
              <Button
                basic
                type="button"
                title={Translate.string('Create new session')}
                icon="plus"
                size="small"
                onClick={() => setSelectedSessionId('draft')}
              />
            </div>
            {selectedSessionId === 'draft' && (
              <SessionCreateForm
                eventId={eventId}
                eventType={eventType}
                onClose={() => setSelectedSessionId(null)}
              />
            )}
            {Number.isInteger(selectedSessionId) && (
              <SessionEditForm
                eventId={eventId}
                eventType={eventType}
                sessionId={selectedSessionId as number}
                onClose={() => setSelectedSessionId(null)}
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
    )
  );
}
