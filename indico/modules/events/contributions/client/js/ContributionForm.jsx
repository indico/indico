// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.manage_contrib_rest';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Button, Dimmer, Form, Loader} from 'semantic-ui-react';

import {
  CollapsibleContainer,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalContributionPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

export function ContributionForm({eventId, contribId, eventTitle, personLinkFieldParams, onClose}) {
  const contribURL = contributionURL(snakifyKeys({eventId, contribId}));
  const {data: contrib, loading} = useIndicoAxios(contribURL);
  const referenceTypes = [{id: 1, name: 'DOI'}, {id: 2, name: 'URL'}, {id: 3, name: 'ISBN'}];

  const handleSubmit = async formData => {
    console.debug('Submitting', {
      ..._.pick(formData, ['title', 'description', 'keywords', 'board_number', 'code']),
      ..._.omit(formData.location_data, 'use_default'),
      inherit_location: !formData.location_data.use_default,
      references: formData.references.map(({id, ...rest}) => rest),
    });
    const resp = await indicoAxios.patch(contribURL, {
      ..._.pick(formData, ['title', 'description', 'keywords', 'board_number', 'code']),
      ..._.omit(formData.location_data, 'use_default'),
      inherit_location: !formData.location_data.use_default,
      references: formData.references.map(({id, ...rest}) => rest),
    });
    console.debug('Response', resp);
  };

  console.debug(contrib, loading, personLinkFieldParams);

  if (loading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  return (
    <FinalModalForm
      id="contribution-form"
      header={Translate.string("Edit contribution '{title}'", {title: contrib.title})}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={{
        person_links: camelizeKeys(contrib.persons),
        location_data: {
          use_default: contrib.inherit_location,
          ..._.pick(contrib, ['venue_name', 'venue_id', 'room_name', 'room_id', 'address']),
        },
        ..._.pick(contrib, [
          'title',
          'description',
          'duration',
          'keywords',
          'board_number',
          'code',
          'references',
        ]),
      }}
      size="small"
    >
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      <FinalDuration name="duration" label={Translate.string('Duration')} />
      <FinalContributionPersonLinkField
        name="person_links"
        label={Translate.string('People')}
        eventId={eventId}
        sessionUser={Indico.User}
        {...personLinkFieldParams}
      />
      <FinalLocationField
        name="location_data"
        label={Translate.string('Location')}
        parent={{title: eventTitle, type: Translate.string('Event')}}
      />
      <FinalTagList
        name="keywords"
        label={Translate.string('Keywords')}
        placeholder={Translate.string('Please enter a keyword')}
      />
      <CollapsibleContainer title={Translate.string('Advanced')} dividing>
        CUSTOM FIELDS HERE!
        <FinalReferences
          name="references"
          label={Translate.string('External IDs')}
          description={Translate.string('Manage external resources for this contribution')}
        />
        <Form.Group widths="equal">
          <FinalInput name="board_number" label={Translate.string('Board number')} />
          <FinalInput name="code" label={Translate.string('Program code')} />
        </Form.Group>
      </CollapsibleContainer>
    </FinalModalForm>
  );
}

ContributionForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  contribId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  personLinkFieldParams: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function EditContributionButton({
  eventId,
  contribId,
  eventTitle,
  personLinkFieldParams,
  triggerSelector,
  ...rest
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Edit contribution</Translate>
        </Button>
      )}
      {open && (
        <ContributionForm
          eventId={eventId}
          contribId={contribId}
          eventTitle={eventTitle}
          personLinkFieldParams={personLinkFieldParams}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

EditContributionButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  contribId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  personLinkFieldParams: PropTypes.object.isRequired,
  triggerSelector: PropTypes.string,
};

EditContributionButton.defaultProps = {
  triggerSelector: null,
};
