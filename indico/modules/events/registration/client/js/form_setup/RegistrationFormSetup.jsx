// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {useSelector} from 'react-redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import {IButton} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {SortableWrapper} from 'indico/react/sortable';

import DisabledSectionsModal from './DisabledSectionsModal';
import {isUILocked, getNestedSections, getDisabledSections} from './selectors';
import SetupFormSection from './SetupFormSection';

import '../../styles/regform.module.scss';

export default function RegistrationFormSetup() {
  const sections = useSelector(getNestedSections);
  const disabledSections = useSelector(getDisabledSections);
  const uiLocked = useSelector(isUILocked);
  const [disabledSectionModalActive, setDisabledSectionModalActive] = useState(false);

  return (
    <Dimmer.Dimmable dimmed={uiLocked}>
      <DndProvider backend={HTML5Backend}>
        {disabledSections.length > 0 && (
          <div className="toolbar" styleName="setup-toolbar">
            <IButton onClick={() => setDisabledSectionModalActive(true)}>
              <Translate>Disabled sections</Translate>
            </IButton>
          </div>
        )}

        <SortableWrapper accept="regform-section" className="regform-section-list">
          {sections.map((section, index) => (
            <SetupFormSection key={section.id} index={index} {...section} setupMode />
          ))}
        </SortableWrapper>
      </DndProvider>

      {disabledSectionModalActive && (
        <DisabledSectionsModal onClose={() => setDisabledSectionModalActive(false)} />
      )}

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
