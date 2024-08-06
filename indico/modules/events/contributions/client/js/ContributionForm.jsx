// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contribFieldsURL from 'indico-url:contributions.api_contrib_fields';
import locationParentContribURL from 'indico-url:contributions.api_contrib_location_parent';
import contribPersonLinkFieldParamsURL from 'indico-url:contributions.api_contrib_person_link_params';
import defaultDurationURL from 'indico-url:contributions.api_contribs_duration';
import locationParentURL from 'indico-url:contributions.api_contribs_location_parent';
import contributionCreateURL from 'indico-url:contributions.api_create_contrib';
import contributionURL from 'indico-url:contributions.api_manage_contrib';
import personLinkFieldParamsURL from 'indico-url:events.api_person_link_params';

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
import {FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

function ContributionForm({
  eventId,
  personLinkFieldParams,
  locationParent,
  customFields,
  onSubmit,
  loading,
  ...rest
}) {
  const handleSubmit = formData => {
    // formData = _.omit(formData, ['person_links']); // TODO person links
    const customFieldsData = Object.entries(formData.custom_fields).map(([key, data]) => ({
      id: parseInt(key.replace('field_', ''), 10),
      data,
    }));
    const personLinks = formData.person_links.map(
      ({
        affiliationMeta,
        avatarURL,
        favoriteUsers,
        fullName,
        id,
        isAdmin,
        language,
        name,
        userId,
        userIdentifier,
        invalid,
        detail,
        ...personLinkData
      }) => ({
        ...personLinkData,
      })
    );
    formData = {
      ...formData,
      custom_fields: customFieldsData,
      person_links: snakifyKeys(personLinks),
    };
    onSubmit({
      ...formData,
      references: formData.references.map(({id, ...refs}) => refs),
    });
  };

  if (loading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const customFieldsSection = customFields.map(
    ({id, fieldType, title, description, isRequired, fieldData}) => {
      const key = `custom_field_${id}`;
      const name = `custom_fields.field_${id}`;
      if (fieldType === 'text') {
        if (fieldData.multiline) {
          return (
            <FinalTextArea
              key={key}
              name={name}
              label={title}
              description={description}
              required={isRequired}
            />
          );
        } else {
          return (
            <FinalInput
              key={key}
              name={name}
              label={title}
              description={description}
              required={isRequired}
            />
          );
        }
      } else if (fieldType === 'single_choice') {
        const options = fieldData.options.map(opt => ({
          key: opt.id,
          text: opt.option,
          value: opt.id,
        }));

        return (
          <FinalDropdown
            key={key}
            name={name}
            label={title}
            description={description}
            required={isRequired}
            options={options}
            selection
          />
        );
      } else {
        console.warn('Unsupported field type', fieldType);
        return null;
      }
    }
  );

  return (
    <FinalModalForm id="contribution-form" onSubmit={handleSubmit} size="small" {...rest}>
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      <FinalDuration name="duration" label={Translate.string('Duration')} />
      <FinalContributionPersonLinkField
        name="person_links"
        label={Translate.string('People')}
        eventId={eventId}
        sessionUser={{...Indico.User, userId: Indico.User.id}}
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
      {customFieldsSection}
      <CollapsibleContainer title={Translate.string('Advanced')} dividing>
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
  personLinkFieldParams: PropTypes.object,
  locationParent: PropTypes.object,
  customFields: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      fieldType: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      isRequired: PropTypes.bool,
      fieldData: PropTypes.shape({
        multiline: PropTypes.bool,
        options: PropTypes.arrayOf(
          PropTypes.shape({id: PropTypes.string.isRequired, option: PropTypes.string.isRequired})
        ),
      }).isRequired,
    })
  ),
  onSubmit: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
};

ContributionForm.defaultProps = {
  personLinkFieldParams: {},
  locationParent: {},
  customFields: [],
};

export function ContributionEditForm({eventId, contribId, onClose}) {
  const {data: personLinkFieldParams, loading: personLinkFieldParamsLoading} = useIndicoAxios(
    contribPersonLinkFieldParamsURL({event_id: eventId, contrib_id: contribId}),
    {camelize: true}
  );
  const {data: fields, loading: fieldsLoading} = useIndicoAxios(
    contribFieldsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentContribURL({event_id: eventId, contrib_id: contribId})
  );
  const contribURL = contributionURL(snakifyKeys({eventId, contribId}));
  const {data: contrib, loading: contribLoading} = useIndicoAxios(contribURL);

  const handleSubmit = async formData => {
    try {
      await indicoAxios.patch(contribURL, formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const loading =
    contribLoading || locationParentLoading || fieldsLoading || personLinkFieldParamsLoading;

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      locationParent={locationParent}
      customFields={fields}
      header={Translate.string("Edit contribution '{title}'", {title: contrib?.title})}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={
        loading
          ? {}
          : {
              ...contrib,
              custom_fields: Object.fromEntries(
                contrib.custom_fields.map(field => [`field_${field.id}`, field.data])
              ),
              person_links: camelizeKeys(contrib.person_links),
            }
      }
      loading={loading}
    />
  );
}

ContributionEditForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  contribId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function ContributionCreateForm({eventId, onClose}) {
  const {data: personLinkFieldParams, loading: personLinkFieldParamsLoading} = useIndicoAxios(
    personLinkFieldParamsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: fields, loading: fieldsLoading} = useIndicoAxios(
    contribFieldsURL({event_id: eventId}),
    {camelize: true}
  );
  const {data: defaultDuration, loading: defaultDurationLoading} = useIndicoAxios(
    defaultDurationURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );

  const handleSubmit = async formData => {
    try {
      await indicoAxios.post(contributionCreateURL({event_id: eventId}), formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};
  const loading =
    locationParentLoading ||
    defaultDurationLoading ||
    fieldsLoading ||
    personLinkFieldParamsLoading;

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      locationParent={locationParent}
      customFields={fields}
      header={Translate.string('Add new contribution')}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={
        loading
          ? {}
          : {
              duration: defaultDuration,
              person_links: [],
              keywords: [],
              references: [],
              location_data: locationData,
              custom_fields: Object.fromEntries(fields.map(field => [`field_${field.id}`, ''])),
            }
      }
      loading={loading}
    />
  );
}

ContributionCreateForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function EditContributionButton({eventId, contribId, eventTitle, triggerSelector, ...rest}) {
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
  triggerSelector: PropTypes.string,
};

EditContributionButton.defaultProps = {
  triggerSelector: null,
};

export function CreateContributionButton({eventId, triggerSelector, ...rest}) {
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
      {open && <ContributionCreateForm eventId={eventId} onClose={() => setOpen(false)} />}
    </>
  );
}

CreateContributionButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  triggerSelector: PropTypes.string,
};

CreateContributionButton.defaultProps = {
  triggerSelector: null,
};
