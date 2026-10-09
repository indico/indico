// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import newTimetableURL from 'indico-url:timetable.management';

import React, {useCallback, useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Modal, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

const LEGACY_TIMETABLE_POPUP_LS_KEY = 'legacy-timetable-popup';

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

      if (storedPopupData.dontShowAgain) {
        return;
      }

      // wait 24h before showing again
      if (new Date().getTime() - storedPopupData.lastShown < 24 * 60 * 60 * 1000) {
        return;
      }

      setPopupData(storedPopupData);
      setPopupVisible(true);
    }
  }, []);

  return (
    <Modal size="tiny" open={popupVisible} onClose={handleClose}>
      <Modal.Header>
        &#x1F389; <Translate>Try out the new timetable!</Translate>
      </Modal.Header>
      <Modal.Content>
        <Translate>
          The Indico team is proud to present a complete redesign of the timetable page! Featuring a
          modern look, it aims to be more intuitive and easy-to-use, while preserving all the
          functionality.
        </Translate>
      </Modal.Content>
      <Modal.Actions>
        <Button negative onClick={handleDontShowAgain}>
          <Translate>Don't show again</Translate>
        </Button>
        <Button positive onClick={handleGoToNewTimetable}>
          <Translate>Try it!</Translate>
        </Button>
        <Button onClick={handleClose}>
          <Translate>Remind me later</Translate>
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
        position="left center"
        onClose={() => setPopupState('hidden')}
        open={popupState === 'animating' || popupState === 'visible'}
        trigger={
          <Button
            primary
            size="tiny"
            href={newTimetableURL({event_id: eventId, set_preference: true})}
          >
            &#x1F389; Try the new timetable
          </Button>
        }
      >
        <Popup.Header>
          &#x1F389; <Translate>New Timetable</Translate>
        </Popup.Header>
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
          ReactDOM.render(
            <NewTimetableButton eventId={parseInt(this.getAttribute('event-id')!, 10)} />,
            this
          );
        });
      }
    }
  );
});
