// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Label} from 'semantic-ui-react';

import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

export function PlacesLeft({placesLimit, placesUsed, isEnabled}) {
  const placesLeft = placesLimit - placesUsed;
  const color = placesLeft > 0 ? (isEnabled ? 'green' : 'grey') : 'red';

  return (
    <Label color={color} style={{whiteSpace: 'nowrap'}}>
      {placesLeft > 0 ? (
        <PluralTranslate count={placesLeft}>
          <Singular>
            <Param name="count" value={placesLeft} /> place left
          </Singular>
          <Plural>
            <Param name="count" value={placesLeft} /> places left
          </Plural>
        </PluralTranslate>
      ) : (
        <Translate>No places left</Translate>
      )}
    </Label>
  );
}

PlacesLeft.propTypes = {
  placesLimit: PropTypes.number.isRequired,
  placesUsed: PropTypes.number.isRequired,
  isEnabled: PropTypes.bool.isRequired,
};
