// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';

import {FinalLocationField} from 'indico/react/components';
import {FinalPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

export default function SessionBlockForm() {
  const [modalOpen, setModalOpen] = useState(false);
  // TODO get this from session:
  const event = {id: 1, title: 'TODO Conference name here'};

  return (
    <>
      <Button onClick={() => setModalOpen(true)}>Open Block Form</Button>
      {modalOpen && (
        <FinalModalForm
          id="session-form"
          header={Translate.string('Edit block ???')}
          onSubmit={() => {}}
          onClose={() => setModalOpen(false)}
          initialValues={{person_links: [], location_data: {use_default: true}}}
        >
          <FinalInput
            name="title"
            label={Translate.string('Title')}
            description={Translate.string('Title of the session block')}
            autoFocus
            required
          />
          <FinalInput name="code" label={Translate.string('Program code')} />
          <FinalPersonLinkField
            name="person_links"
            label={Translate.string('Conveners')}
            eventId={event.id}
            sessionUser={Indico.User}
          />
          <FinalTextArea name="description" label={Translate.string('Description')} />
          <FinalLocationField
            name="location_data"
            label={Translate.string('Location')}
            parent={{title: event.title, type: Translate.string('Event')}}
          />
        </FinalModalForm>
      )}
    </>
  );
}
