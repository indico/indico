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
import {Icon, Layout, Row, Col, Menu} from 'antd';

import {Translate} from 'indico/react/i18n';
import UserActions from '../containers/UserActions';

import './App.module.scss';


const {Header, Content} = Layout;

export default function App() {
    return (
        <Layout>
            <Header styleName="rb-menu-bar">
                <Col span={6}>
                    <h1>
                        <Icon type="home" />
                        <Translate>Room Booking</Translate>
                    </h1>
                </Col>
                <Col span={12}>
                    <Menu mode="horizontal" theme="dark" styleName="rb-menu">
                        <Menu.Item styleName="rb-menu-item">
                            <Icon type="plus-circle-o" />
                            <Translate>Book a Room</Translate>
                        </Menu.Item>
                        <Menu.Item styleName="rb-menu-item">
                            <Icon type="profile" />
                            <Translate>List of Rooms</Translate>
                        </Menu.Item>
                        <Menu.Item styleName="rb-menu-item">
                            <Icon type="schedule" />
                            <Translate>Calendar</Translate>
                        </Menu.Item>
                        <Menu.Item styleName="rb-menu-item">
                            <Icon type="close-circle-o" />
                            <Translate>Blockings</Translate>
                        </Menu.Item>
                    </Menu>
                </Col>
                <Col span={6}>
                    <Row type="flex" justify="end">
                        <UserActions />
                    </Row>
                </Col>
            </Header>
            <Content styleName="rb-content">
                New Room Booking
            </Content>
        </Layout>
    );
}
