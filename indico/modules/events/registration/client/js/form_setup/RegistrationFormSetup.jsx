// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Form as FinalForm} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Dimmer, Loader} from 'semantic-ui-react';

import {IButton} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {SortableWrapper} from 'indico/react/sortable';

import {getNestedSections, getItems} from '../form/selectors';

import DisabledSectionsModal from './DisabledSectionsModal';
import SectionSettingsModal from './SectionSettingsModal';
import {isUILocked, getDisabledSections} from './selectors';
import SetupFormSection from './SetupFormSection';

import '../../styles/regform.module.scss';

export default function RegistrationFormSetup() {
  const sections = useSelector(getNestedSections);
  const disabledSections = useSelector(getDisabledSections);
  const items = useSelector(getItems);
  const uiLocked = useSelector(isUILocked);
  const [disabledSectionModalActive, setDisabledSectionModalActive] = useState(false);
  const [addSectionModalActive, setAddSectionModalActive] = useState(false);

  const initialValues = Object.fromEntries(
    Object.entries(items).map(([, {htmlName, defaultValue}]) => [htmlName, defaultValue])
  );

  return (
    <Dimmer.Dimmable dimmed={uiLocked}>
      <DndProvider backend={HTML5Backend}>
        <div className="toolbar" styleName="setup-toolbar">
          <IButton icon="plus" onClick={() => setAddSectionModalActive(true)}>
            <Translate>Add section</Translate>
          </IButton>
          {disabledSections.length > 0 && (
            <IButton onClick={() => setDisabledSectionModalActive(true)}>
              <Translate>Disabled sections</Translate>
            </IButton>
          )}
        </div>

        {/* we need a dummy FinalForm so our fields don't break... */}
        <FinalForm
          initialValues={initialValues}
          subscription={{initialValues: true}}
          onSubmit={() => undefined}
        >
          {fprops => {
            // FinalForm does not propagate changes to initialValues immediately.
            // The first render contains the old initialValues, which is a problem for
            // newly added fields whose initialValue becomes undefined.
            // Thus, we filter out all fields that have no corresponding value until
            // the updated initiaValues become available.
            const currentSections = sections.map(section => ({
              ...section,
              items: section.items.filter(item => item.htmlName in fprops.initialValues),
            }));

            return (
              <SortableWrapper accept="regform-section" className="regform-section-list">
                {currentSections.map((section, index) => (
                  <SetupFormSection key={section.id} index={index} {...section} setupMode />
                ))}
              </SortableWrapper>
            );
          }}
        </FinalForm>
      </DndProvider>

      {addSectionModalActive && (
        <SectionSettingsModal onClose={() => setAddSectionModalActive(false)} />
      )}
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
