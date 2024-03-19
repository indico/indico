// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Icon} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {entrySchema, handleUnimplemented} from '../util';

export default function AttachmentsDisplay({entry}) {
  const {attachmentCount} = entry;
  return (
    <p>
      <Translate as="strong">Materials</Translate>: <Icon name="paperclip" />
      {attachmentCount > 0 ? (
        <PluralTranslate count={attachmentCount}>
          <Singular>
            <Param name="count" value={attachmentCount} /> file
          </Singular>
          <Plural>
            <Param name="count" value={attachmentCount} /> files
          </Plural>
        </PluralTranslate>
      ) : (
        <Translate as="em">None</Translate>
      )}
      <Icon
        name="pencil"
        color="grey"
        className="right"
        title={Translate.string('Manage materials')}
        onClick={handleUnimplemented}
        link
      />
    </p>
  );
}

AttachmentsDisplay.propTypes = {
  entry: entrySchema.isRequired,
};
