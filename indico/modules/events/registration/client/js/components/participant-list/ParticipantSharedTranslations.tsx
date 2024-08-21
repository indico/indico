// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';

export function ParticipantCountHidden({count}: {count: number}) {
  return (
    <PluralTranslate count={count}>
      <Singular>
        <Param name="count" value={count} /> participant registered anonymously.
      </Singular>
      <Plural>
        <Param name="count" value={count} /> participants registered anonymously.
      </Plural>
    </PluralTranslate>
  );
}
