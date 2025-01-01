// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {ConnectedRouter} from 'connected-react-router';
import PropTypes from 'prop-types';
import React from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import MediaQuery from 'react-responsive';
import {Link, Redirect, Route, Switch} from 'react-router-dom';
import {Dimmer, Header, Icon, Loader, Segment, Sidebar} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {ConditionalRoute} from 'indico/react/util';

import * as globalActions from '../actions';
import {actions as configActions} from '../common/config';
import {LinkBar} from '../common/linking';
import {actions as mapActions} from '../common/map';
import {actions as roomsActions} from '../common/rooms';
import {actions as userActions} from '../common/user';
import ModalController from '../modals';
import AdminArea from '../modules/admin';
import BlockingList from '../modules/blockings';
import BookRoom from '../modules/bookRoom';
import Calendar from '../modules/calendar';
import Landing from '../modules/landing';
import RoomList from '../modules/roomList';
import * as globalSelectors from '../selectors';

import AdminOverrideBar from './AdminOverrideBar';
import AdminOverrideShortcut from './AdminOverrideShortcut';
import Menu from './Menu';
import SidebarMenu, {SidebarTrigger} from './SidebarMenu';
import './App.module.scss';

class App extends React.Component {
  static propTypes = {
    title: PropTypes.string,
    iconName: PropTypes.string,
    history: PropTypes.object.isRequired,
    filtersSet: PropTypes.bool.isRequired,
    isInitializing: PropTypes.bool.isRequired,
    fetchInitialData: PropTypes.func.isRequired,
    resetPageState: PropTypes.func.isRequired,
    renderExtraRoutes: PropTypes.func,
  };

  static defaultProps = {
    title: Translate.string('Room Booking'),
    iconName: 'home',
    renderExtraRoutes: () => null,
  };

  state = {
    userActionsVisible: false,
  };

  componentDidMount() {
    const {fetchInitialData} = this.props;
    fetchInitialData();
  }

  onSidebarHide = () => {
    document.body.classList.remove('scrolling-disabled');
    this.setState({userActionsVisible: false});
  };

  renderContent() {
    const {filtersSet, isInitializing, renderExtraRoutes} = this.props;
    const {userActionsVisible} = this.state;
    return (
      <Sidebar.Pushable styleName="rb-pushable">
        <SidebarMenu visible={userActionsVisible} onClickOption={this.onSidebarHide} />
        <Sidebar.Pusher dimmed={userActionsVisible} styleName="rb-pusher">
          <div styleName="rb-content">
            <Switch>
              <Route
                exact
                path="/"
                render={({location}) => (
                  <Redirect to={{pathname: '/book', search: location.search}} />
                )}
              />
              <ConditionalRoute
                path="/book"
                render={({location, match: {isExact}}) =>
                  filtersSet ? (
                    <BookRoom location={location} />
                  ) : isExact ? (
                    <Landing />
                  ) : (
                    <Redirect to="/book" />
                  )
                }
                active={!isInitializing}
              />
              <ConditionalRoute path="/rooms" component={RoomList} active={!isInitializing} />
              <ConditionalRoute
                path="/blockings"
                component={BlockingList}
                active={!isInitializing}
              />
              <ConditionalRoute path="/calendar" component={Calendar} active={!isInitializing} />
              <ConditionalRoute path="/admin" component={AdminArea} active={!isInitializing} />
              {renderExtraRoutes(isInitializing)}
              <Route
                render={() => (
                  <Segment placeholder>
                    <Header icon color="red">
                      <Icon name="exclamation triangle" />
                      <Translate>This page does not exist.</Translate>
                    </Header>
                  </Segment>
                )}
              />
            </Switch>
            <ModalController />
          </div>
        </Sidebar.Pusher>
      </Sidebar.Pushable>
    );
  }

  render() {
    const {title, history, iconName, resetPageState, isInitializing} = this.props;
    const {userActionsVisible} = this.state;

    return (
      <ConnectedRouter history={history}>
        <div styleName="rb-layout">
          <header styleName="rb-menu-bar">
            <div styleName="rb-menu-bar-side-left">
              <h1>
                <Link to="/" onClick={() => resetPageState('bookRoom')}>
                  <Icon name={iconName} />
                  <MediaQuery as="span" minWidth={500}>
                    {title}
                  </MediaQuery>
                </Link>
              </h1>
            </div>
            <div styleName="rb-menu-bar-menu">
              <Overridable id="Menu">
                <Menu />
              </Overridable>
            </div>
            <div styleName="rb-menu-bar-side-right">
              <SidebarTrigger
                onClick={evt => {
                  document.body.classList.add('scrolling-disabled');
                  this.setState({
                    userActionsVisible: true,
                  });
                  // XXX: for some reason react 17 immediately closes the sidebar again after
                  // opening it, but stopping the click event from propagating avoids this, so it's
                  // likely related to the changes in event handling
                  evt.stopPropagation();
                }}
                active={userActionsVisible}
              />
            </div>
          </header>
          <AdminOverrideBar />
          <AdminOverrideShortcut />
          {!isInitializing && <LinkBar />}
          {this.renderContent()}
          <Dimmer.Dimmable>
            <Dimmer active={isInitializing} page>
              <Loader />
            </Dimmer>
          </Dimmer.Dimmable>
        </div>
      </ConnectedRouter>
    );
  }
}

export default connect(
  state => ({
    filtersSet: globalSelectors.filtersAreSet(state),
    isInitializing: globalSelectors.isInitializing(state),
  }),
  dispatch => ({
    fetchInitialData() {
      dispatch(configActions.fetchConfig()).then(() => {
        // we only need map areas if the map is enabled, which depends on the config
        dispatch(mapActions.fetchAreas());
      });
      dispatch(userActions.fetchUserInfo());
      dispatch(userActions.fetchFavoriteRooms());
      dispatch(userActions.fetchAllRoomPermissions());
      dispatch(roomsActions.fetchEquipmentTypes());
      dispatch(roomsActions.fetchRooms());
    },
    resetPageState(namespace) {
      dispatch(globalActions.resetPageState(namespace));
    },
  })
)(Overridable.component('App', App));
