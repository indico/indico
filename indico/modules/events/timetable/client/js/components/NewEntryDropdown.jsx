// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {useDispatch} from 'react-redux';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as actions from '../actions';
import {entryTypes} from '../util';

export default function NewEntryDropdown(props) {
  const dispatch = useDispatch();

  return (
    <Dropdown {...props}>
      <Dropdown.Menu>
        <Dropdown.Header content={Translate.string('Add new')} />
        {['session', 'contribution', 'break'].map(newType => {
          const {title, icon} = entryTypes[newType];
          const handleClick = () => dispatch(actions.addEntry(newType));
          return <Dropdown.Item key={newType} text={title} icon={icon} onClick={handleClick} />;
        })}
      </Dropdown.Menu>
    </Dropdown>
  );
}
