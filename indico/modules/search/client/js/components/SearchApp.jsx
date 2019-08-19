// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ResultList from './ResultList';
import './SearchApp.module.scss';

export default function SearchApp() {
  return (
    <div styleName="search">
      <ResultList />
    </div>
  );
}
