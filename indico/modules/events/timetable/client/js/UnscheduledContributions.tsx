// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {Moment} from 'moment';
import React, {useEffect, useMemo, useRef, useState} from 'react';
import {useSelector} from 'react-redux';
import {Button} from 'semantic-ui-react';

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
          color={contrib.backgroundColor}
          textColor={contrib.textColor}
        />
      ))}
    </div>
  );
}

export default function UnscheduledContributions({dt}: {dt: Moment}) {
  const contribs = useSelector(selectors.getUnscheduled);
  const sessions = useSelector(selectors.getSessions);
  const showUnscheduled = useSelector(selectors.showUnscheduled);
  const wrapperRef = useRef(null);

  const [selectedFilter, setSelectedFilter] = useState('no-session');

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

  function hasContribs(sessionId: string) {
    return contribs.some(c => c.sessionId === parseInt(sessionId, 10));
  }

  const currentContribs = useMemo(() => {
    if (selectedFilter === 'no-session') {
      return contribs.filter(c => !c.sessionId);
    }
    return contribs.filter(c => c.sessionId === parseInt(selectedFilter, 10));
  }, [contribs, selectedFilter]);

  if (!showUnscheduled) {
    return null;
  }

  return (
    <>
      <div
        styleName="contributions-container"
        style={{height: '100%', overflow: 'hidden'}}
        ref={wrapperRef}
      >
        <div
          styleName="content"
          style={{overflowX: 'auto', maxHeight: '100%', padding: '1em 1em 5em 0'}}
        >
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '.5em',
              marginBottom: '2em',
            }}
          >
            <Button
              primary={selectedFilter === 'no-session'}
              type="button"
              onClick={() => setSelectedFilter('no-session')}
            >
              No assigned session
            </Button>
            {Object.entries(sessions)
              .filter(([id]) => hasContribs(id))
              .map(([id, session]) => (
                <Button
                  key={id}
                  type="button"
                  primary={selectedFilter === id}
                  onClick={() => setSelectedFilter(id)}
                >
                  <span style={{display: 'flex', gap: '.5em', alignItems: 'center'}}>
                    <span>{session.title}</span>
                    <span
                      style={{
                        borderRadius: '50%',
                        backgroundColor: session.backgroundColor,
                        width: '1em',
                        height: '1em',
                      }}
                    />
                  </span>
                </Button>
              ))}
          </div>

          <UnscheduledContributionList dt={dt} contribs={currentContribs} />
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
