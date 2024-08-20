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
