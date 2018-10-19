/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import React from 'react';
import PropTypes from 'prop-types';
import {Link, Redirect, Route, Switch} from 'react-router-dom';
import {ConnectedRouter} from 'connected-react-router';
import {Dimmer, Icon, Loader} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {Overridable, RouteAwareOverridable} from 'indico/react/util';
import UserActions from '../components/UserActions';
import Landing from '../modules/landing';
import Calendar from '../modules/calendar';
import BookRoom from '../modules/bookRoom';
import RoomList from '../modules/roomList';
import BlockingList from '../modules/blockings';
import ModalController from '../modals';
import Menu from './Menu';

import './App.module.scss';


function ConditionalRoute({active, component, render, ...props}) {
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
    component: PropTypes.oneOfType([PropTypes.func, PropTypes.element]),
    render: PropTypes.func,
};

ConditionalRoute.defaultProps = {
    component: null,
    render: null,
};


export default class App extends React.Component {
    static propTypes = {
        title: PropTypes.string,
        iconName: PropTypes.string,
        history: PropTypes.object.isRequired,
        filtersSet: PropTypes.bool.isRequired,
        isInitializing: PropTypes.bool.isRequired,
        fetchInitialData: PropTypes.func.isRequired,
        resetPageState: PropTypes.func.isRequired
    };

    static defaultProps = {
        title: Translate.string('Room Booking'),
        iconName: 'home'
    };

    componentDidMount() {
        const {fetchInitialData} = this.props;
        fetchInitialData();
    }

    render() {
        const {title, history, iconName, filtersSet, resetPageState, isInitializing} = this.props;

        return (
            <ConnectedRouter history={history}>
                <div styleName="rb-layout">
                    <header styleName="rb-menu-bar">
                        <div styleName="rb-menu-bar-side-left">
                            <h1>
                                <Icon name={iconName} />
                                <Link to="/" onClick={() => resetPageState('bookRoom')}>
                                    {title}
                                </Link>
                            </h1>
                        </div>
                        <div styleName="rb-menu-bar-menu">
                            <RouteAwareOverridable id="Menu">
                                <Menu />
                            </RouteAwareOverridable>
                        </div>
                        <div styleName="rb-menu-bar-side-right">
                            <UserActions />
                        </div>
                    </header>
                    <div styleName="rb-content">
                        <Switch>
                            <Route exact path="/" render={() => <Redirect to="/book" />} />
                            <ConditionalRoute path="/book" render={({location, match: {isExact}}) => (
                                filtersSet
                                    ? (
                                        <Overridable id="BookRoom">
                                            <BookRoom location={location} />
                                        </Overridable>
                                    ) : (
                                        isExact ? <Landing /> : <Redirect to="/book" />
                                    )
                            )} active={!isInitializing} />
                            <ConditionalRoute path="/rooms" component={RoomList} active={!isInitializing} />
                            <ConditionalRoute path="/blockings" component={BlockingList} active={!isInitializing} />
                            <ConditionalRoute path="/calendar" component={Calendar} active={!isInitializing} />
                        </Switch>
                        <ModalController />
                    </div>
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
