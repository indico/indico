// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// TODO: This file should be removed once the legacy timetable is removed

import newTimetableURL from 'indico-url:timetable.management';

import React, {useCallback, useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Icon, Modal, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './legacy.module.scss';

const LEGACY_TIMETABLE_POPUP_LS_KEY = 'legacy-timetable-popup';
const POPUP_REMINDER_DELAY = 86400 * 1000;

type PopupState = 'hidden' | 'animating' | 'visible';

interface PopupData {
  dontShowAgain: boolean;
  lastShown: number;
}

function NewTimetableDialog({eventId, onClose}: {eventId: number; onClose?: () => void}) {
  const [popupVisible, setPopupVisible] = useState(false);
  const [popupData, setPopupData] = useState<Partial<PopupData>>({dontShowAgain: false});

  const handleClose = useCallback(() => {
    localStorage.setItem(
      LEGACY_TIMETABLE_POPUP_LS_KEY,
      JSON.stringify({...popupData, lastShown: new Date().getTime()})
    );
    setPopupVisible(false);
    onClose?.();
  }, [popupData, onClose]);

  const handleDontShowAgain = useCallback(() => {
    localStorage.setItem(
      LEGACY_TIMETABLE_POPUP_LS_KEY,
      JSON.stringify({...popupData, dontShowAgain: true})
    );
    setPopupVisible(false);
    onClose?.();
  }, [popupData, onClose]);

  const handleGoToNewTimetable = useCallback(() => {
    localStorage.setItem(
      LEGACY_TIMETABLE_POPUP_LS_KEY,
      JSON.stringify({...popupData, dontShowAgain: true})
    );
    setPopupVisible(false);
    location.href = newTimetableURL({event_id: eventId, set_preference: true});
  }, [popupData, eventId]);

  useEffect(() => {
    const popupDataString = localStorage.getItem(LEGACY_TIMETABLE_POPUP_LS_KEY);

    if (popupDataString === null) {
      setPopupVisible(true);
    } else {
      let storedPopupData: PopupData;
      try {
        storedPopupData = JSON.parse(popupDataString);
      } catch {
        return;
      }

      const currentTime = new Date().getTime();
      const timeElapsedSincePopupShown = currentTime - (storedPopupData.lastShown ?? 0);
      if (storedPopupData.dontShowAgain || timeElapsedSincePopupShown < POPUP_REMINDER_DELAY) {
        return;
      }

      setPopupData(storedPopupData);
      setPopupVisible(true);
    }
  }, []);

  return (
    <Modal size="tiny" open={popupVisible} onClose={handleClose} closeIcon>
      <Modal.Content>
        <h2 style={{color: 'black', fontWeight: 'bold'}}>
          🎉 <Translate>Try out the new timetable!</Translate>
        </h2>
        <strong
          style={{
            color: '#f0f',
            fontFamily: 'Comic Sans MS',
            fontSize: '1.5em',
          }}
        >
          TODO - add an image here instead of this text!
        </strong>
        <br />
        The Indico team is proud to present a complete redesign of the timetable page! Featuring a
        modern look, it aims to be more intuitive and easy-to-use, while preserving all the
        functionality.
      </Modal.Content>
      <Modal.Actions>
        <Button styleName="dont-show-again" onClick={handleDontShowAgain}>
          <Translate>Don't show again</Translate>
        </Button>
        <Button positive onClick={handleGoToNewTimetable}>
          <Translate>Try it!</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}

function NewTimetableButton({eventId}: {eventId: number}) {
  const [popupState, setPopupState] = useState<PopupState>('hidden');

  useEffect(() => {
    if (popupState === 'animating') {
      const id = setTimeout(() => setPopupState('visible'), 500);
      return () => clearTimeout(id);
    }
  }, [popupState]);

  return (
    <>
      <Popup
        style={{
          opacity: popupState === 'visible' ? 1 : 0,
          transition: 'opacity 0.5s ease-in-out',
        }}
        inverted
        position="left center"
        onClose={() => setPopupState('hidden')}
        open={popupState === 'animating' || popupState === 'visible'}
        trigger={
          <Button
            primary
            styleName="try-new-timetable"
            size="tiny"
            href={newTimetableURL({event_id: eventId, set_preference: true})}
          >
            <Translate>Try the new timetable</Translate>
            <Icon name="arrow right" />
          </Button>
        }
      >
        <Popup.Content>
          <Translate>You can still try out the new timetable by pressing this button.</Translate>
        </Popup.Content>
      </Popup>
      <NewTimetableDialog eventId={eventId} onClose={() => setPopupState('animating')} />
    </>
  );
}

document.addEventListener('DOMContentLoaded', () => {
  customElements.define(
    'ind-new-timetable-button',
    class extends HTMLElement {
      connectedCallback() {
        requestAnimationFrame(() => {
          ReactDOM.render(<NewTimetableButton eventId={+this.getAttribute('event-id')!} />, this);
        });
      }
    }
  );
});
