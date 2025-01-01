// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Icon, Popup} from 'semantic-ui-react';

import {Translate, Param} from 'indico/react/i18n';

import {actions as userActions, selectors as userSelectors} from '../common/user';

import './AdminOverrideBar.module.scss';

const AdminOverrideBar = ({visible, disable}) => {
  if (!visible) {
    return null;
  }

  const trigger = (
    <span>
      <Icon name="exclamation triangle" />
      <Translate>Admin override enabled</Translate>.{' '}
      <Translate>
        Use{' '}
        <Param
          name="shortcut"
          value={
            <>
              <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>A</kbd>
            </>
          }
        />{' '}
        to toggle.
      </Translate>
    </span>
  );

  return (
    <header styleName="admin-override-bar">
      <Popup trigger={trigger}>
        <Translate>
          While in Admin Override mode, you can book any room regardless of restrictions and edit
          any booking.
        </Translate>
      </Popup>
      <span styleName="disable" onClick={disable}>
        <Popup trigger={<Icon name="close" />} position="top right" offset={[10, 0]}>
          <Translate>Disable admin override</Translate>
        </Popup>
      </span>
    </header>
  );
};

AdminOverrideBar.propTypes = {
  visible: PropTypes.bool.isRequired,
  disable: PropTypes.func.isRequired,
};

export default connect(
  state => ({
    visible: userSelectors.isUserAdminOverrideEnabled(state),
  }),
  dispatch => ({
    disable: bindActionCreators(userActions.toggleAdminOverride, dispatch),
  })
)(AdminOverrideBar);
