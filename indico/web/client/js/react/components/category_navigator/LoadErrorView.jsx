// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Translate} from 'indico/react/i18n';

import {useCategoryNavigator} from './context';

export default function LoadErrorView() {
  const {navigatorState} = useCategoryNavigator();

  const handleGoHome = evt => {
    evt.preventDefault();
    navigatorState.navigateTo(0);
  };

  return (
    <div className="placeholder">
      <div className="placeholder-text">
        <Translate>Failed to load category</Translate>
      </div>
      <div className="placeholder-help">
        <Translate>
          This could be due to a server error or because the category is protected.
        </Translate>{' '}
        <button type="button" className="link-action" onClick={handleGoHome}>
          <Translate>Go to the home category</Translate>
        </button>
      </div>
    </div>
  );
}
