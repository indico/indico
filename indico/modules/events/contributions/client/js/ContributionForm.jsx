// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Button, Form} from 'semantic-ui-react';

import {
  CollapsibleContainer,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

export default function ContributionForm() {
  const [modalOpen, setModalOpen] = useState(false);
  // TODO get this from session:
  const event = {id: 1, title: 'TODO Conference name here'};
  const referenceTypes = [{id: 1, name: 'DOI'}, {id: 2, name: 'URL'}, {id: 3, name: 'ISBN'}];

  return (
    <>
      <Button onClick={() => setModalOpen(true)}>Open Contribution Form</Button>
      {modalOpen && (
        <FinalModalForm
          id="contribution-form"
          header={Translate.string("Edit contribution '{contribution}'", {contribution: 'TODO'})}
          onSubmit={() => {}}
          onClose={() => setModalOpen(false)}
          initialValues={{
            person_links: [],
            location_data: {use_default: true},
            keywords: [],
            references: [],
          }}
          size="small"
        >
          <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
          <FinalTextArea name="description" label={Translate.string('Description')} />
          <FinalPersonLinkField
            name="person_links"
            label={Translate.string('Conveners')}
            eventId={event.id}
            sessionUser={Indico.User}
          />
          <FinalLocationField
            name="location_data"
            label={Translate.string('Location')}
            parent={{title: event.title, type: Translate.string('Event')}}
          />
          <FinalTagList
            name="keywords"
            label={Translate.string('Keywords')}
            placeholder={Translate.string('Please enter a keyword')}
          />
          <CollapsibleContainer title={Translate.string('Advanced')} dividing>
            CUSTOM FIELDS HERE!
            {referenceTypes.length > 0 && (
              <FinalReferences
                name="references"
                label={Translate.string('External IDs')}
                description={Translate.string('Manage external resources for this contribution')}
                referenceTypes={referenceTypes}
              />
            )}
            <Form.Group widths="equal">
              <FinalInput name="board_number" label={Translate.string('Board number')} />
              <FinalInput name="code" label={Translate.string('Program code')} />
            </Form.Group>
          </CollapsibleContainer>
        </FinalModalForm>
      )}
    </>
  );
}
