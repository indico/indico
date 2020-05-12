// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Icon, Sidebar, Menu} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {push as pushRoute} from 'connected-react-router';
import Overridable from 'react-overridable';
import {Translate} from 'indico/react/i18n';

import {selectors as userSelectors, actions as userActions} from '../common/user';
import {actions as blockingsActions} from '../modules/blockings';
import {actions as filtersActions} from '../common/filters';
import * as globalActions from '../actions';
import SidebarFooter from './SidebarFooter';

import './SidebarMenu.module.scss';

export function SidebarTrigger({onClick, active}) {
  const icon = <Icon name="bars" size="large" />;
  // The icon can only be wrapped by the 'trigger' element if it's clickable,
  // otherwise the 'click outside' event would be caught both by the EventStack
  // in SUI's Sidebar component and the trigger's onClick handler (and silently
  // cancel itself)
  return (
    <div className={active ? 'active' : ''} styleName="sidebar-button">
      {active ? icon : <div onClick={onClick}>{icon}</div>}
    </div>
  );
}

SidebarTrigger.propTypes = {
  onClick: PropTypes.func.isRequired,
  active: PropTypes.bool.isRequired,
};

function SidebarMenu({
  isAdmin,
  isAdminOverrideEnabled,
  hasOwnedRooms,
  gotoMyBookings,
  gotoBookingsInMyRooms,
  gotoMyRoomsList,
  gotoMyBlockings,
  gotoRBAdminArea,
  toggleAdminOverride,
  visible,
  onClickOption,
  hideOptions,
  extraOptions,
}) {
  const options = [
    {
      key: 'my_bookings',
      icon: 'list alternate outline',
      text: Translate.string('My Bookings'),
      onClick: gotoMyBookings,
    },
    {
      key: 'bookings_my_rooms',
      icon: 'checkmark',
      text: Translate.string('Bookings in My Rooms'),
      onClick: gotoBookingsInMyRooms,
      onlyIf: hasOwnedRooms,
    },
    {
      key: 'my_rooms',
      icon: 'user',
      text: Translate.string('List of My Rooms'),
      onClick: gotoMyRoomsList,
      onlyIf: hasOwnedRooms,
    },
    {
      key: 'my_blockings',
      icon: 'window close outline',
      text: Translate.string('My Blockings'),
      onClick: gotoMyBlockings,
      onlyIf: !hideOptions.myBlockings,
    },
    {
      key: 'isAdmin',
      icon: 'cogs',
      text: Translate.string('Administration'),
      onClick: gotoRBAdminArea,
      onlyIf: isAdmin,
    },
    {
      key: 'adminOverride',
      icon: isAdminOverrideEnabled ? 'unlock' : 'lock',
      text: Translate.string('Admin Override'),
      iconColor: isAdminOverrideEnabled ? 'orange' : undefined,
      active: isAdminOverrideEnabled,
      onClick: toggleAdminOverride,
      onlyIf: isAdmin,
    },
  ]
    .concat(extraOptions)
    .filter(
      ({onlyIf}) =>
        onlyIf === undefined ||
        (_.isFunction(onlyIf) ? onlyIf({isAdmin, isAdminOverrideEnabled, hasOwnedRooms}) : onlyIf)
    );

  return (
    <Sidebar
      as={Menu}
      animation="overlay"
      icon="labeled"
      vertical
      width="thin"
      direction="right"
      onHide={onClickOption}
      inverted
      visible={visible}
      styleName="sidebar"
    >
      {options.map(({key, text, icon, onClick, iconColor, active}) => {
        return (
          <Menu.Item
            as="a"
            key={key}
            active={active}
            onClick={() => {
              onClick();
              if (onClickOption) {
                onClickOption();
              }
            }}
          >
            <Icon name={icon} color={iconColor} />
            {text}
          </Menu.Item>
        );
      })}
      <div styleName="bottom-align">
        <SidebarFooter />
      </div>
    </Sidebar>
  );
}

SidebarMenu.propTypes = {
  extraOptions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
    })
  ),
  isAdmin: PropTypes.bool.isRequired,
  isAdminOverrideEnabled: PropTypes.bool.isRequired,
  hasOwnedRooms: PropTypes.bool.isRequired,
  gotoMyBookings: PropTypes.func.isRequired,
  gotoBookingsInMyRooms: PropTypes.func.isRequired,
  gotoMyRoomsList: PropTypes.func.isRequired,
  gotoMyBlockings: PropTypes.func.isRequired,
  gotoRBAdminArea: PropTypes.func.isRequired,
  toggleAdminOverride: PropTypes.func.isRequired,
  visible: PropTypes.bool,
  onClickOption: PropTypes.func,
  hideOptions: PropTypes.objectOf(PropTypes.bool),
};

SidebarMenu.defaultProps = {
  extraOptions: [],
  visible: false,
  onClickOption: null,
  hideOptions: {},
};

export default connect(
  state => ({
    isAdmin: userSelectors.isUserRBAdmin(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    hasOwnedRooms: userSelectors.hasOwnedRooms(state),
  }),
  dispatch => ({
    // ATTENTION: this is **intentionally** passed as a prop, despite not being used,
    // so that plugins can dispatch actions.
    dispatch,
    gotoMyBookings() {
      dispatch(globalActions.resetPageState('calendar'));
      dispatch(
        filtersActions.setFilters(
          'calendar',
          {
            myBookings: true,
            hideUnused: true,
          },
          false
        )
      );
      dispatch(pushRoute('/calendar?my_bookings=true&hide_unused=true'));
    },
    gotoBookingsInMyRooms() {
      dispatch(globalActions.resetPageState('calendar'));
      dispatch(
        filtersActions.setFilters(
          'calendar',
          {
            onlyMine: true,
            hideUnused: true,
          },
          false
        )
      );
      dispatch(pushRoute('/calendar?mine=true&hide_unused=true'));
    },
    gotoMyRoomsList() {
      dispatch(globalActions.resetPageState('roomList'));
      dispatch(filtersActions.setFilters('roomList', {onlyMine: true}, false));
      dispatch(pushRoute('/rooms?mine=true'));
    },
    gotoMyBlockings() {
      dispatch(globalActions.resetPageState('blockings'));
      dispatch(blockingsActions.setFilters({myBlockings: true}, false));
      dispatch(pushRoute('/blockings?my_blockings=true'));
    },
    gotoRBAdminArea() {
      dispatch(pushRoute('/admin'));
    },
    toggleAdminOverride() {
      dispatch(userActions.toggleAdminOverride());
    },
  })
)(Overridable.component('SidebarMenu', SidebarMenu));
