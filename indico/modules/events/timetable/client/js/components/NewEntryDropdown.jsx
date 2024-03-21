// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {entryTypes, handleUnimplemented} from '../util';

export default function NewEntryDropdown(props) {
  return (
    <Dropdown {...props}>
      <Dropdown.Menu>
        <Dropdown.Header content={Translate.string('Add new')} />
        {['session', 'contribution', 'break'].map(newType => (
          <Dropdown.Item
            key={newType}
            text={entryTypes[newType].title}
            icon={entryTypes[newType].icon}
            onClick={handleUnimplemented}
          />
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}
