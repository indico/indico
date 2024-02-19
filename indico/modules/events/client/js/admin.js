// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import autoLinkerRulesURL from 'indico-url:events.autolinker_rules';

import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Loader} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';

import AutoLinkerConfig from './components/AutoLinkerConfig';
import AutoLinkerTestDrive from './components/AutoLinkerTestDrive';

function AutoLinker() {
  const [_rules, setRules] = useState(null);
  const {data, loading} = useIndicoAxios(autoLinkerRulesURL(), {
    camelize: true,
  });

  const rules = _rules || data?.rules;

  return loading ? (
    <Loader />
  ) : (
    <>
      <AutoLinkerConfig rules={rules} onChange={setRules} />
      <AutoLinkerTestDrive rules={rules} />
    </>
  );
}

window.setupAutoLinkerConfig = rootElementId => {
  const rootElement = document.getElementById(rootElementId);

  if (rootElement) {
    ReactDOM.render(<AutoLinker />, rootElement);
  }
};
