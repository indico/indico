// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {useCategoryNavigator} from './context';

export default function Breadcrumbs({path}) {
  const {navigatorState} = useCategoryNavigator();

  if (!path || !path.length) {
    return null;
  }

  return (
    <div className="breadcrumb">
      <span className="breadcrumb-prefix">In: </span>
      {path.map((category, idx) => (
        <span key={category.id}>
          <button
            type="button"
            className="breadcrumb-item"
            onClick={() => navigatorState.navigateTo(category.id)}
            value="drill-up"
          >
            {category.title}
          </button>
          {idx < path.length - 1 && (
            <span className="breadcrumb-separator" aria-hidden="true">
              {' '}
              »{' '}
            </span>
          )}
        </span>
      ))}
    </div>
  );
}

Breadcrumbs.propTypes = {
  path: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
    })
  ),
};
