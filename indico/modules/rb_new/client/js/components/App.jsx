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
import {Link, Route, Switch} from 'react-router-dom';
import {ConnectedRouter} from 'react-router-redux';
import {Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import UserActions from '../containers/UserActions';
import Landing from '../containers/Landing';
import Calendar from './pages/Calendar';
import BookRoom from '../containers/BookRoom';
import RoomList from '../containers/RoomList';
import BlockingList from './pages/BlockingList';
import Menu from './Menu';

import './App.module.scss';


export default function App({history}) {
    return (
        <ConnectedRouter history={history}>
            <div styleName="rb-layout">
                <header styleName="rb-menu-bar">
                    <div styleName="rb-menu-bar-side-left">
                        <h1>
                            <Icon name="home" />
                            <Link to="/">
                                <Translate>Room Booking</Translate>
                            </Link>
                        </h1>
                    </div>
                    <div styleName="rb-menu-bar-menu">
                        <Menu />
                    </div>
                    <div styleName="rb-menu-bar-side-right">
                        <UserActions />
                    </div>
                </header>
                <div styleName="rb-content">
                    <Switch>
                        <Route exact path="/" component={Landing} />
                        <Route path="/book" component={BookRoom} />
                        <Route path="/rooms" component={RoomList} />
                        <Route path="/blockings" component={BlockingList} />
                        <Route path="/calendar" component={Calendar} />
                    </Switch>
                </div>
            </div>
        </ConnectedRouter>
    );
}

App.propTypes = {
    history: PropTypes.object.isRequired
};
