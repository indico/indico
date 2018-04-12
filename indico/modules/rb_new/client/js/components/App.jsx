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
import {BrowserRouter, Link, Route, Switch} from 'react-router-dom';
import {Icon, Layout, Row, Col} from 'antd';

import {Translate} from 'indico/react/i18n';
import UserActions from '../containers/UserActions';
import Landing from './pages/Landing';
import BookRoom from './pages/BookRoom';
import Calendar from './pages/Calendar';
import RoomList from '../containers/RoomList';
import BlockingList from './pages/BlockingList';
import Menu from './Menu';

import './App.module.scss';


const {Header, Content} = Layout;


export default function App() {
    return (
        <BrowserRouter basename="/rooms_new">
            <Layout>
                <Header styleName="rb-menu-bar">
                    <Col span={6}>
                        <h1>
                            <Icon type="home" />
                            <Link to="/">
                                <Translate>Room Booking</Translate>
                            </Link>
                        </h1>
                    </Col>
                    <Col span={12}>
                        <Menu />
                    </Col>
                    <Col span={6}>
                        <Row type="flex" justify="end">
                            <UserActions />
                        </Row>
                    </Col>
                </Header>
                <Content styleName="rb-content">
                    <Switch>
                        <Route exact path="/" component={Landing} />
                        <Route path="/book" component={BookRoom} />
                        <Route path="/rooms" component={RoomList} />
                        <Route path="/blockings" component={BlockingList} />
                        <Route path="/calendar" component={Calendar} />
                    </Switch>
                </Content>
            </Layout>
        </BrowserRouter>
    );
}
