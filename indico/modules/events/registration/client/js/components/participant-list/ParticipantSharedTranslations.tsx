// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

interface ParticipantCountHiddenProps {
  count: number;
  countHidden: number;
}

export function ParticipantCountHidden({count, countHidden}: ParticipantCountHiddenProps) {
  return (
    <div>
      <PluralTranslate count={countHidden}>
        <Singular>
          <Param name="count" value={countHidden} /> participant registered anonymously.
        </Singular>
        <Plural>
          <Param name="count" value={countHidden} /> participants registered anonymously.
        </Plural>
      </PluralTranslate>{' '}
      <Translate>
        Total amount of participants is <Param name="total" value={count} />.
      </Translate>
    </div>
  );
}
