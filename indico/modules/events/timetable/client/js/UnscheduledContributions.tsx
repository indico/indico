// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';
import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useSelector} from 'react-redux';
import {Button, Label, Select} from 'semantic-ui-react';

import SessionEditForm, {SessionCreateForm} from 'indico/modules/events/sessions/SessionForm';
import {Translate} from 'indico/react/i18n';

import * as selectors from './selectors';
import './UnscheduledContributions.module.scss';
import {DraggableUnscheduledContributionEntry} from './UnscheduledContributionEntry';

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

  const [selectedFilter, setSelectedFilter] = useState<string | 'no-session'>('no-session');
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
        initialPosition.current = e.pageX;
        wrapperRef.current.style.width = `${width}px`;
      }
    }

    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mousemove', onMouseMove);
    return () => {
      document.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mousemove', onMouseMove);
    };
  }, []);

  const currentContribs = useMemo(() => {
    return contribsGrouped[selectedFilter] ?? [];
  }, [contribs, selectedFilter]);

  if (!showUnscheduled) {
    return null;
  }

  let dropdownSessions = Object.entries(sessions).map(([id, session]) => ({
    value: +id,
    text: (
      <div styleName="session" style={{fontSize: '0.8em'}}>
        <Label
          empty
          circular
          style={{
            ...session.colors,
            width: '0.8em',
            height: '0.8em',
            fontWeight: 'normal',
          }}
        />
        {session.title} ({contribsGrouped[id]?.length})
      </div>
    ),
  }));

  dropdownSessions = dropdownSessions.toSorted((s1, s2) => {
    const l1 = (contribsGrouped[s1.value] ?? []).length;
    const l2 = (contribsGrouped[s2.value] ?? []).length;

    return l1 && l2 ? 0 : Math.sign(l2 - l1);
  });

  // TODO: (Ajob) Once we move to an approach where we have all kinds of draft blocks
  //              I propose we have some kind of filter option to search by entry type,
  //              session, etc. If no filters are applied, everything is visible.
  return (
    <>
      <div
        styleName="contributions-container"
        style={{height: '100%', overflow: 'hidden'}}
        ref={wrapperRef}
      >
        <div
          styleName="content"
          style={{overflowX: 'auto', height: '100%', padding: '1em 1em 5em 0'}}
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <div styleName="actions">
              {/* TODO: (Ajob) This design is not great, but reworking the side-bar
                               will be part of a separate PR.
              */}
              <Select
                button
                defaultValue="no-session"
                onChange={(_, {value}) => setSelectedFilter(value)}
                options={[
                  {
                    value: 'no-session',
                    text: (
                      <div styleName="session" style={{fontSize: '0.8em'}}>
                        <Label
                          empty
                          circular
                          color="grey"
                          style={{
                            width: '0.8em',
                            height: '0.8em',
                            fontWeight: 'normal',
                          }}
                        />
                        <Translate>No assigned session</Translate>
                      </div>
                    ),
                  },
                  ...dropdownSessions,
                ]}
              />
              {Number.isInteger(+selectedFilter) && (
                <Button
                  basic
                  type="button"
                  title={Translate.string('Edit selected session')}
                  icon="edit"
                  size="mini"
                  disabled={!Number.isInteger(+selectedFilter)}
                  onClick={() => setDraftSessionId(+selectedFilter)}
                />
              )}
              <Button
                basic
                type="button"
                title={Translate.string('Create new session')}
                icon="plus"
                size="mini"
                onClick={() => setDraftSessionId('new')}
              />
            </div>
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
