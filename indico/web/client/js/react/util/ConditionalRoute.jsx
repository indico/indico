// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Route} from 'react-router-dom';

export default function ConditionalRoute({active, component, render, ...props}) {
  const routeProps = {};
  if (component) {
    routeProps.component = active ? component : null;
  } else if (render) {
    routeProps.render = active ? render : null;
  } else {
    throw new Error('either "component" or "render" should be provided as a prop');
  }

  return <Route {...props} {...routeProps} />;
}

ConditionalRoute.propTypes = {
  active: PropTypes.bool.isRequired,
  component: PropTypes.elementType,
  render: PropTypes.func,
};

ConditionalRoute.defaultProps = {
  component: null,
  render: null,
};
