// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {useSelector} from 'react-redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {SortableWrapper} from 'indico/react/sortable';

import {isUILocked, getNestedSections} from './selectors';
import SetupFormSection from './SetupFormSection';

export default function RegistrationFormSetup() {
  const items = useSelector(getNestedSections);
  const uiLocked = useSelector(isUILocked);

  return (
    <Dimmer.Dimmable dimmed={uiLocked}>
      <DndProvider backend={HTML5Backend}>
        <SortableWrapper accept="regform-section" className="regform-section-list">
          {items.map((section, index) => (
            <SetupFormSection key={section.id} index={index} {...section} setupMode />
          ))}
        </SortableWrapper>
      </DndProvider>

      <Dimmer inverted active={uiLocked}>
        <Loader size="massive">
          {/*
            XXX this loader and text may not be visible since it's vertically centered,
            inside the dimmable and in case of larger registration forms it may be outside
            the currently visible area.
            an alternative would be using the dimmer, but showing the save indicator in a
            static place on the page, e.g. like we do in the cornerMessage util
          */}
          <Translate>Saving...</Translate>
        </Loader>
      </Dimmer>
    </Dimmer.Dimmable>
  );
}
