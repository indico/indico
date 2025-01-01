// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import {useEffect, useCallback} from 'react';
import {connect} from 'react-redux';

import {actions as userActions, selectors as userSelectors} from '../common/user';

export function AdminOverrideShortcut({isAdmin, toggleAdminOverride}) {
  const handleAdminKeypress = useCallback(
    event => {
      if (event.ctrlKey && event.shiftKey && event.key === 'A') {
        if (isAdmin) {
          event.preventDefault();
          toggleAdminOverride();
        }
      }
    },
    [isAdmin, toggleAdminOverride]
  );

  useEffect(() => {
    window.addEventListener('keydown', handleAdminKeypress);
    return () => {
      window.removeEventListener('keydown', handleAdminKeypress);
    };
  }, [handleAdminKeypress]);

  return null;
}

AdminOverrideShortcut.propTypes = {
  isAdmin: PropTypes.bool.isRequired,
  toggleAdminOverride: PropTypes.func.isRequired,
};

export default connect(
  state => ({
    isAdmin: userSelectors.isUserRBAdmin(state),
  }),
  dispatch => ({
    toggleAdminOverride: () => dispatch(userActions.toggleAdminOverride()),
  })
)(AdminOverrideShortcut);
