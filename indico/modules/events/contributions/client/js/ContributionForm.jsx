// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// import contributionURL from 'indico-url:contributions.manage_contrib_rest';
import locationParentContribURL from 'indico-url:contributions.api_contrib_location_parent';
import defaultDurationURL from 'indico-url:contributions.api_contribs_duration';
import locationParentURL from 'indico-url:contributions.api_contribs_location_parent';
import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import contributionURL from 'indico-url:contributions.api_manage_contrib';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {FormSpy} from 'react-final-form';
import {Button, Dimmer, Form, Loader, Message, MessageHeader} from 'semantic-ui-react';

import {
  CollapsibleContainer,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
} from 'indico/react/components';
import {FinalContributionPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

export function ContributionEditForm({eventId, contribId, personLinkFieldParams, onClose}) {
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentContribURL({event_id: eventId, contrib_id: contribId})
  );
  const contribURL = contributionURL(snakifyKeys({eventId, contribId}));
  const {data: contrib, loading} = useIndicoAxios(contribURL);

  const handleSubmit = async formData => {
    formData = _.omit(formData, ['person_links', 'custom_fields']); // TODO person links, custom fields
    try {
      await indicoAxios.patch(contribURL, {
        ...formData,
        references: formData.references.map(({id, ...rest}) => rest),
      });
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  if (loading || locationParentLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  console.log(contrib);

  return (
    <FinalModalForm
      id="contribution-form"
      header={Translate.string("Edit contribution '{title}'", {title: contrib.title})}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={{
        ...contrib,
        person_links: camelizeKeys(contrib.person_links),
      }}
      size="small"
    >
      <FormSpy subscription={{values: true, errors: true}}>
        {({values, errors}) => {
          console.log(values, errors);
          return null;
        }}
      </FormSpy>
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
        locationParent={locationParent}
      />
      <FinalTagList
        name="keywords"
        label={Translate.string('Keywords')}
        placeholder={Translate.string('Please enter a keyword')}
      />
      <CollapsibleContainer title={Translate.string('Advanced')} dividing>
        <Message negative>
          <MessageHeader>TODO: Implement custom contribution fields</MessageHeader>
        </Message>
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

ContributionEditForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  contribId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  personLinkFieldParams: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function ContributionCreateForm({eventId, personLinkFieldParams, onClose}) {
  const {data: defaultDuration, loading: defaultDurationLoading} = useIndicoAxios(
    defaultDurationURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );

  const handleSubmit = async formData => {
    formData = _.omit(formData, ['person_links', 'custom_fields']); // TODO person links, custom fields
    try {
      await indicoAxios.post(contributionCreateURL({event_id: eventId}), {
        ...formData,
        references: formData.references.map(({id, ...rest}) => rest),
      });
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  if (locationParentLoading || defaultDurationLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};

  return (
    <FinalModalForm
      id="contribution-form"
      header={Translate.string('Add new contribution')}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={{
        duration: defaultDuration,
        person_links: [],
        keywords: [],
        references: [],
        location_data: locationData,
      }}
      size="small"
    >
      <FormSpy subscription={{values: true, errors: true}}>
        {({values, errors}) => {
          console.log(values, errors);
          return null;
        }}
      </FormSpy>
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
        locationParent={locationParent}
      />
      <FinalTagList
        name="keywords"
        label={Translate.string('Keywords')}
        placeholder={Translate.string('Please enter a keyword')}
      />
      <CollapsibleContainer title={Translate.string('Advanced')} dividing>
        <Message negative>
          <MessageHeader>TODO: Implement custom contribution fields</MessageHeader>
        </Message>
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

ContributionCreateForm.propTypes = {
  eventId: PropTypes.number.isRequired,
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
        <ContributionEditForm
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

export function CreateContributionButton({
  eventId,
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
        <ContributionCreateForm
          eventId={eventId}
          personLinkFieldParams={personLinkFieldParams}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

CreateContributionButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  personLinkFieldParams: PropTypes.object.isRequired,
  triggerSelector: PropTypes.string,
};

CreateContributionButton.defaultProps = {
  triggerSelector: null,
};
