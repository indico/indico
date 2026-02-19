// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchAffiliationsURL from 'indico-url:event_registration.search_registration_affiliation';

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';

import {FinalAffiliationField} from 'indico/react/components';
import {FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getStaticData} from '../selectors';

import './AffiliationInput.module.scss';

const AFFILIATION_MODES = {
  both: 1,
  predefined: 2,
  custom: 3,
};

export default function AffiliationInput({
  fieldId,
  htmlId,
  htmlName,
  disabled,
  isRequired,
  affiliationMode,
  searchContext,
}) {
  const {hasPredefinedAffiliations, eventId, regformId} = useSelector(getStaticData);
  const usePredefinedAffiliations =
    hasPredefinedAffiliations && affiliationMode !== AFFILIATION_MODES.custom;

  return (
    <FinalAffiliationField
      id={htmlId}
      name={htmlName}
      styleName="affiliation-field"
      hasPredefinedAffiliations={usePredefinedAffiliations}
      allowCustomAffiliations={affiliationMode !== AFFILIATION_MODES.predefined}
      searchAffiliationURL={({q}) =>
        searchAffiliationsURL({
          event_id: eventId,
          reg_form_id: regformId,
          field_id: fieldId,
          q,
          ...searchContext,
        })
      }
      required={isRequired}
      disabled={disabled}
      validate={value =>
        isRequired && !value?.text ? Translate.string('This field is required.') : undefined
      }
      includeMeta
    />
  );
}

AffiliationInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool.isRequired,
  affiliationMode: PropTypes.oneOf(Object.values(AFFILIATION_MODES)).isRequired,
  searchContext: PropTypes.object,
};

AffiliationInput.defaultProps = {
  disabled: false,
  searchContext: {},
};

export const affiliationSettingsInitialData = {
  affiliationMode: AFFILIATION_MODES.both,
};

export function AffiliationSettings() {
  const {hasPredefinedAffiliations} = useSelector(getStaticData);
  if (!hasPredefinedAffiliations) {
    return null;
  }
  return (
    <FinalDropdown
      name="affiliationMode"
      label={Translate.string('Allowed affiliations')}
      options={[
        {
          value: AFFILIATION_MODES.both,
          text: Translate.string('Predefined and custom affiliations'),
        },
        {
          value: AFFILIATION_MODES.predefined,
          text: Translate.string('Only predefined affiliations'),
        },
        {value: AFFILIATION_MODES.custom, text: Translate.string('Only custom affiliations')},
      ]}
      search={false}
      selection
      required
      fluid
    />
  );
}
