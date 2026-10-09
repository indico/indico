// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import legacyTimetableURL from 'indico-url:timetable.management-legacy';

import React, {useEffect, useState} from 'react';
import {Popup, Menu, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

const NEW_TIMETABLE_POPUP_LS_KEY = 'new-timetable-popup';

type PopupState = 'hidden' | 'animating' | 'visible';

export function LegacyTimetableSwitchButton({eventId}: {eventId: number}) {
  const [popupState, setPopupState] = useState<PopupState>('hidden');

  useEffect(() => {
    if (popupState === 'animating') {
      localStorage.setItem(NEW_TIMETABLE_POPUP_LS_KEY, 'true');
      const id = setTimeout(() => setPopupState('visible'), 500);
      return () => clearTimeout(id);
    }
  }, [popupState]);

  useEffect(() => {
    const popupDataString = localStorage.getItem(NEW_TIMETABLE_POPUP_LS_KEY);
    if (popupDataString !== 'true') {
      setPopupState('animating');
    }
  }, []);

  return (
    <Popup
      style={{opacity: popupState === 'visible' ? 1 : 0, transition: 'opacity 0.5s ease-in-out'}}
      onClose={() => setPopupState('hidden')}
      onOpen={() => setPopupState('visible')}
      open={popupState === 'animating' || popupState === 'visible'}
      on="hover"
      trigger={
        <Menu.Item
          style={{marginTop: 'auto'}}
          color="brown"
          href={legacyTimetableURL({event_id: eventId, set_preference: true})}
        >
          <Icon name="arrow left" size="large" />
        </Menu.Item>
      }
    >
      <Popup.Header>
        <Translate>Old Timetable</Translate>
      </Popup.Header>
      <Popup.Content>
        <Translate>You can use this button to switch to the old timetable.</Translate>
      </Popup.Content>
    </Popup>
  );
}
