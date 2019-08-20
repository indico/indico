// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Button} from 'semantic-ui-react';
import ResultList from './ResultList';

import './SearchApp.module.scss';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import File from './results/File';

export default function SearchApp() {
  const [active, setActive] = useState('category');
  return (
    <div>
      <Button.Group widths="4">
        <Button
          toggle
          active={active === 'category'}
          className={active === 'category' ? 'ui blue button' : 'ui red button'}
          onClick={() => setActive('category')}
        >
          Category
        </Button>
        <Button toggle active={active === 'contribution'} onClick={() => setActive('contribution')}>
          Contribution
        </Button>
        <Button toggle active={active === 'event'} onClick={() => setActive('event')}>
          Event
        </Button>
        <Button toggle active={active === 'file'} onClick={() => setActive('file')}>
          File
        </Button>
      </Button.Group>
      {active === 'category' && <ResultList component={Category} />}
      {active === 'contribution' && <ResultList component={Contribution} />}
      {active === 'event' && <ResultList component={Event} />}
      {active === 'file' && <ResultList component={File} />}
    </div>
  );
}
