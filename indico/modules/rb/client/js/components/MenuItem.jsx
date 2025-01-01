// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Link, Route} from 'react-router-dom';

import * as globalActions from '../actions';

import './MenuItem.module.scss';

function MenuItem({namespace, path, children, resetPageState}) {
  return (
    <Route path={path}>
      {({match}) => (
        <li className={match ? 'selected' : ''} styleName="rb-menu-item">
          <Link to={path} onClick={() => resetPageState(namespace)}>
            {children}
          </Link>
        </li>
      )}
    </Route>
  );
}

MenuItem.propTypes = {
  namespace: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  resetPageState: PropTypes.func.isRequired,
};

export default connect(
  null,
  dispatch => ({
    resetPageState(namespace) {
      dispatch(globalActions.resetPageState(namespace));
    },
  })
)(MenuItem);
