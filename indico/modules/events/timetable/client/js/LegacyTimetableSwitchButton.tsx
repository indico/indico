// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import legacyTimetableURL from 'indico-url:timetable.management-legacy';

import React, {useCallback, useEffect, useState} from 'react';
import {Popup, Menu, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

const NEW_TIMETABLE_POPUP_LS_KEY = 'new-timetable-popup';

export function LegacyTimetableSwitchButton({eventId}: {eventId: number}) {
  const [popupOpen, setPopupOpen] = useState(false);
  const [popupOpening, setPopupOpening] = useState(false);

  const openPopup = useCallback(() => {
    setPopupOpening(true);
  }, []);

  const closePopup = useCallback(() => {
    setPopupOpening(false);
    setPopupOpen(false);
  }, []);

  useEffect(() => {
    if (popupOpening) {
      setPopupOpen(true);
    }
  }, [popupOpening]);

  useEffect(() => {
    // HACK: wait for the timetable to finish its layout
    const popupDataString = localStorage.getItem(NEW_TIMETABLE_POPUP_LS_KEY);
    if (popupDataString !== 'true') {
      localStorage.setItem(NEW_TIMETABLE_POPUP_LS_KEY, 'true');
      setTimeout(() => openPopup(), 500);
    }
  }, [openPopup]);

  return (
    <Popup
      style={{opacity: popupOpen ? 1 : 0, transition: 'opacity 0.5s ease-in-out'}}
      onClose={closePopup}
      onOpen={() => setPopupOpen(true)}
      open={popupOpen || popupOpening}
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
        <Icon name="arrow left" />
        <Translate>Old Timetable</Translate>
      </Popup.Header>
      <Popup.Content>
        <Translate>You can use this button to switch to the old timetable.</Translate>
      </Popup.Content>
    </Popup>
  );
}
