// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {push as pushRoute} from 'connected-react-router';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useRef} from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {Link} from 'react-router-dom';
import {Icon, Sidebar, Menu, Ref} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import * as globalActions from '../actions';
import {actions as filtersActions} from '../common/filters';
import {selectors as userSelectors, actions as userActions} from '../common/user';
import {actions as blockingsActions} from '../modules/blockings';

import SidebarFooter from './SidebarFooter';

import './SidebarMenu.module.scss';

export function SidebarTrigger({onClick, active, triggerRef}) {
  return (
    <button
      type="button"
      ref={triggerRef}
      className={active ? 'active' : ''}
      styleName="sidebar-button"
      aria-expanded={active}
      onClick={onClick}
      onKeyDown={event => {
        if (active && event.key === 'Escape') {
          onClick(event);
        }
      }}
    >
      <Icon name="bars" size="large" />
      <span styleName="visually-hidden">
        {active ? <Translate>Close menu</Translate> : <Translate>Open menu</Translate>}
      </span>
    </button>
  );
}

SidebarTrigger.propTypes = {
  triggerRef: PropTypes.object.isRequired,
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
  gotoRBLocationArea,
  isRBLocationManager,
  toggleAdminOverride,
  visible,
  onClickOption,
  onBlur,
  hideOptions,
  extraOptions,
}) {
  const sidebarRef = useRef(null);
  const options = [
    {
      key: 'my_bookings',
      to: '/calendar?my_bookings=true&hide_unused=true',
      icon: 'list alternate outline',
      text: Translate.string('My Bookings'),
      onClick: gotoMyBookings,
    },
    {
      key: 'bookings_my_rooms',
      to: '/calendar?mine=true&hide_unused=true',
      icon: 'checkmark',
      text: Translate.string('Bookings in My Rooms'),
      onClick: gotoBookingsInMyRooms,
      onlyIf: hasOwnedRooms,
    },
    {
      key: 'my_rooms',
      to: '/rooms?mine=true',
      icon: 'user',
      text: Translate.string('List of My Rooms'),
      onClick: gotoMyRoomsList,
      onlyIf: hasOwnedRooms,
    },
    {
      key: 'my_blockings',
      to: '/blockings?my_blockings=true',
      icon: 'window close outline',
      text: Translate.string('My Blockings'),
      onClick: gotoMyBlockings,
      onlyIf: !hideOptions.myBlockings,
    },
    {
      key: 'my_locations',
      to: '/admin/locations',
      icon: 'location arrow',
      text: Translate.string('My Locations'),
      onClick: gotoRBLocationArea,
      onlyIf: isRBLocationManager,
    },
    {
      key: 'isAdmin',
      to: '/admin',
      icon: 'cogs',
      text: Translate.string('Administration'),
      onClick: gotoRBAdminArea,
      onlyIf: isAdmin,
    },
    {
      key: 'adminOverride',
      icon: isAdminOverrideEnabled ? 'unlock' : 'lock',
      text: Translate.string('Admin Override'),
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
    <Ref innerRef={sidebarRef}>
      <Sidebar
        as={Menu}
        animation="overlay"
        icon="labeled"
        vertical
        width="thin"
        direction="right"
        onHide={(event, data) => {
          if (visible) {
            onClickOption?.(event, data);
          }
        }}
        onBlur={onBlur}
        onVisible={() => {
          const sidebar = sidebarRef.current;
          const top = Math.max(0, sidebar.parentElement.getBoundingClientRect().top);
          sidebar.style.setProperty('--sidebar-top', `${top}px`);
        }}
        onShow={() => sidebarRef.current.querySelector('a, button, input')?.focus()}
        onKeyDown={event => {
          if (event.defaultPrevented) {
            return;
          }
          if (event.key === 'Escape') {
            event.preventDefault();
            onClickOption?.();
          } else if (
            event.key === 'Tab' &&
            event.shiftKey &&
            event.target === event.currentTarget.querySelector('a[href], button, input')
          ) {
            event.preventDefault();
            onClickOption?.();
          }
        }}
        inverted
        visible={visible}
        styleName="sidebar"
      >
        {options.map(({key, text, icon, onClick, iconColor, active, to}) => {
          if (key === 'adminOverride') {
            return (
              <Menu.Item as="label" key={key} active={active} styleName="override">
                <input
                  type="checkbox"
                  checked={active}
                  styleName="visually-hidden"
                  onChange={() => {
                    onClick();
                    onClickOption?.();
                  }}
                />
                <Icon name={icon} color={iconColor} />
                {text}
                {active && (
                  <span styleName="active-indicator">
                    <span styleName="visually-hidden">
                      {' '}
                      <Translate>active</Translate>
                    </span>
                  </span>
                )}
              </Menu.Item>
            );
          }
          return (
            <Menu.Item
              as={to ? Link : 'button'}
              to={to}
              type={to ? undefined : 'button'}
              key={key}
              active={active}
              onClick={event => {
                if (to && (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey)) {
                  return;
                }
                event.preventDefault();
                onClick();
                onClickOption?.();
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
    </Ref>
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
  gotoRBLocationArea: PropTypes.func.isRequired,
  isRBLocationManager: PropTypes.bool.isRequired,
  toggleAdminOverride: PropTypes.func.isRequired,
  visible: PropTypes.bool,
  onClickOption: PropTypes.func,
  onBlur: PropTypes.func,
  hideOptions: PropTypes.objectOf(PropTypes.bool),
};

SidebarMenu.defaultProps = {
  extraOptions: [],
  visible: false,
  onClickOption: null,
  onBlur: null,
  hideOptions: {},
};

export default connect(
  state => ({
    isAdmin: userSelectors.isUserRBAdmin(state),
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    hasOwnedRooms: userSelectors.hasOwnedRooms(state),
    isRBLocationManager: userSelectors.isUserRBLocationManager(state),
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
            hideUsed: false,
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
            hideUsed: false,
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
    gotoRBLocationArea() {
      dispatch(pushRoute('/admin/locations'));
    },
    toggleAdminOverride() {
      dispatch(userActions.toggleAdminOverride());
    },
  })
)(Overridable.component('SidebarMenu', SidebarMenu));
