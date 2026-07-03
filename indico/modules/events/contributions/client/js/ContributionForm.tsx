// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
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

import {FormApi} from 'final-form';
import _ from 'lodash';
import moment from 'moment';
import React, {useEffect, useState} from 'react';
import {Field} from 'react-final-form';
import {Button, Dimmer, Form, Icon, Loader} from 'semantic-ui-react';

import {
  UNSCHEDULED_CONTRIB_EDIT_MODAL,
  useModal,
} from 'indico/modules/events/timetable/ModalContext';
import {
  CollapsibleContainer,
  FinalLocationField,
  FinalReferences,
  FinalTagList,
  FinalContributionPersonLinkField,
} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, getChangedValues, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

interface CustomField {
  id: number;
  fieldType: string;
  title: string;
  description: string;
  isRequired: boolean;
  fieldData: {
    multiline?: boolean;
    options?: {id: string; option: string}[];
  };
}

interface ContributionFormProps {
  eventId: number;
  personLinkFieldParams?: Record<string, any>;
  locationParent?: Record<string, any>;
  customFields: CustomField[];
  onSubmit: (formData: any, form?: any) => void;
  initialValues: Record<string, any>;
  sessionBlock?: Record<string, any>;
  loading: boolean;
  [key: string]: any; // Allow additional props
}

interface ContributionFormFieldsProps {
  eventId: number;
  locationParent?: Record<string, any>;
  personLinkFieldParams?: Record<string, any>;
  initialValues: Record<string, any>;
  customFields?: CustomField[];
  extraOptions?: Record<string, any>;
  [key: string]: any; // Allow additional props
}

const referenceIsIncomplete = ref => !ref.type || !ref.value;

export function ContributionFormFields({
  eventId,
  locationParent = {inheriting: false},
  personLinkFieldParams = {},
  initialValues = {},
  customFields = [],
  extraOptions = {},
}: ContributionFormFieldsProps) {
  const [hasIncompleteReferences, setHasIncompleteReferences] = useState(false);
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
      } else if (fieldType === 'single_choice' && fieldData.options) {
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

  const {minStartDt, maxEndDt} = extraOptions;

  return (
    <>
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      {initialValues.start_dt ? (
        <>
          <Field name="duration" subscription={{value: true}}>
            {({input: {value: duration}}) => (
              <FinalDateTimePicker
                name="start_dt"
                label={Translate.string('Start date')}
                minStartDt={minStartDt}
                maxEndDt={maxEndDt ? maxEndDt.clone().subtract(duration, 'seconds') : null}
                required
              />
            )}
          </Field>
          <Field name="start_dt" subscription={{value: true}}>
            {({input: {value: startDt}}) => (
              <FinalDuration
                name="duration"
                label={Translate.string('Duration')}
                max={maxEndDt ? moment(maxEndDt).diff(startDt, 'seconds') : null}
              />
            )}
          </Field>
        </>
      ) : (
        <FinalDuration name="duration" label={Translate.string('Duration')} />
      )}
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
          label={
            <>
              <Translate>External IDs</Translate>
              {hasIncompleteReferences && (
                <span style={{display: 'block', color: '#ba8e23', marginTop: '0.5em'}}>
                  <Icon name="warning sign" />
                  <Translate>
                    Some external IDs are incomplete, and therefore will not be saved on submission.
                  </Translate>
                </span>
              )}
            </>
          }
          onChange={refs => {
            refs.map(ref => {
              if (typeof ref.id === 'string') {
                delete ref.id;
              }
              return ref;
            });
            const incompleteRefs = refs.some(
              ref => ref.type + ref.value !== '' && referenceIsIncomplete(ref)
            );

            if (incompleteRefs !== hasIncompleteReferences) {
              setHasIncompleteReferences(incompleteRefs);
            }

            return refs;
          }}
          description={Translate.string('Manage external resources for this contribution')}
        />
        <Form.Group widths="equal">
          <FinalInput name="board_number" label={Translate.string('Board number')} />
          <FinalInput name="code" label={Translate.string('Program code')} />
        </Form.Group>
      </CollapsibleContainer>
    </>
  );
}

export function ContributionForm({
  eventId,
  personLinkFieldParams = {},
  locationParent = {},
  customFields = [],
  onSubmit,
  initialValues = {},
  sessionBlock = null,
  loading,
  ...rest
}: ContributionFormProps) {
  const handleSubmit = (formData: any, form: FormApi) => {
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
      }) =>
        snakifyKeys({
          ...personLinkData,
        })
    );
    formData = {
      ...formData,
      custom_fields: customFieldsData,
      person_links: personLinks,
      references: formData.references.filter(ref => !referenceIsIncomplete(ref)),
    };
    onSubmit(
      {
        ...formData,
        references: formData.references.map(({id, ...refs}: any) => refs),
      },
      form
    );
  };

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
      onSubmit={handleSubmit}
      initialValues={initialValues}
      size="small"
      {...rest}
    >
      <ContributionFormFields
        eventId={eventId}
        {...{locationParent, initialValues, sessionBlock, customFields, personLinkFieldParams}}
      />
    </FinalModalForm>
  );
}

export function ContributionEditForm({
  eventId,
  contribId,
  onSubmit,
  onClose,
}: {
  eventId: number;
  contribId: number;
  onSubmit?: (formData: any, form: any) => void;
  onClose: () => void;
}) {
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

  const handleSubmit = async (formData: any, form) => {
    try {
      await indicoAxios.patch(contribURL, getChangedValues(formData, form));
    } catch (e) {
      return handleSubmitError(e);
    }

    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
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
      onSubmit={onSubmit ?? handleSubmit}
      onClose={onClose}
      initialValues={
        loading
          ? {}
          : {
              ..._.omit(contrib, 'session_block'),
              custom_fields: Object.fromEntries(
                contrib.custom_fields.map((field: any) => [`field_${field.id}`, field.data])
              ),
              person_links: camelizeKeys(contrib.person_links),
            }
      }
      sessionBlock={camelizeKeys(contrib?.session_block)}
      loading={loading}
    />
  );
}

export function ContributionCreateForm({
  eventId,
  onClose,
  onCreate,
  customFields = {},
  customInitialValues = {},
}: {
  eventId: number;
  onClose: () => void;
  onCreate?: (contrib: any) => void;
  customFields?: Record<string, any>;
  customInitialValues?: Record<string, any>;
}) {
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

  const handleSubmit = async (formData: any) => {
    try {
      const response = await indicoAxios.post(contributionCreateURL({event_id: eventId}), {
        ...formData,
        event_id: eventId,
      });

      if (response.data) {
        onCreate?.(response.data);
      } else {
        location.reload();
      }
    } catch (e) {
      return handleSubmitError(e);
    }

    onClose();
  };

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};
  const loading =
    locationParentLoading ||
    defaultDurationLoading ||
    fieldsLoading ||
    personLinkFieldParamsLoading;

  const initialValues = loading
    ? {}
    : {
        duration: defaultDuration,
        person_links: [],
        keywords: [],
        references: [],
        location_data: locationData,
        custom_fields: {
          ...Object.fromEntries(fields.map((field: any) => [`field_${field.id}`, ''])),
          ...customFields,
        },
        ...customInitialValues,
      };

  return (
    <ContributionForm
      eventId={eventId}
      personLinkFieldParams={personLinkFieldParams}
      locationParent={locationParent}
      customFields={(fields ?? []).concat(Object.values(customFields))}
      header={Translate.string('Add new contribution')}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={initialValues}
      loading={loading}
    />
  );
}

export function EditContributionButton({
  eventId,
  contribId,
  eventTitle,
  triggerSelector,
  trigger,
  ...rest
}: {
  eventId: number;
  contribId: number;
  eventTitle: string;
  triggerSelector?: string;
  trigger?: React.ReactElement;
}) {
  const [open, setOpen] = useState(false);
  const modalContext = useModal();

  const openEditModal = React.useCallback(() => {
    if (modalContext) {
      modalContext.openModal(UNSCHEDULED_CONTRIB_EDIT_MODAL, {
        eventId,
        contribId,
      });
    } else {
      setOpen(true);
    }
  }, [modalContext, eventId, contribId]);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }

    const element = document.querySelector(triggerSelector);

    if (!element) {
      console.error(`No element matched ${triggerSelector}`);
      return;
    }

    element.addEventListener('click', openEditModal);
    return () => element.removeEventListener('click', openEditModal);
  }, [triggerSelector, openEditModal]);

  return (
    <>
      {!triggerSelector &&
        (trigger ? (
          React.cloneElement(trigger, {
            ...trigger.props,
            onClick: e => {
              e.stopPropagation();
              trigger.props.onClick?.(e);
              openEditModal();
            },
          })
        ) : (
          <Button onClick={openEditModal} {...rest}>
            <Translate>Edit contribution</Translate>
          </Button>
        ))}

      {!modalContext && open && (
        <ContributionEditForm
          eventId={eventId}
          contribId={contribId}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

export function CreateContributionButton({
  eventId,
  triggerSelector,
  ...rest
}: {
  eventId: number;
  triggerSelector?: string;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    if (!element) {
      console.error(`No element matched ${triggerSelector}`);
      return;
    }

    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Create contribution</Translate>
        </Button>
      )}
      {open && (
        <ContributionCreateForm
          eventId={eventId}
          onClose={() => setOpen(false)}
          customFields={{}}
          customInitialValues={{}}
        />
      )}
    </>
  );
}
