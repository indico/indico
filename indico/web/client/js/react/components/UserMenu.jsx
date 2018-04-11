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

/* eslint "react/forbid-component-props": "off" */

import React from 'react';
import propTypes from 'prop-types';
import {Avatar, Divider, Icon, Select} from 'antd';

// TODO: Remove this once ThiefMaster's done
window.build_url = (data) => JSON.stringify(data);

import userDashboard from 'indico-url:users.user_dashboard';
import userPreferences from 'indico-url:users.user_preferences';
import authLogout from 'indico-url:auth.logout';
import changeLanguage from 'indico-url:core.change_lang';

import {Translate} from 'indico/react/i18n';
import {Slot, ContainerDiv, ContainerBound} from 'indico/react/util';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import ArrowDownMenu from './ArrowDownMenu';
import './UserMenu.module.scss';


async function postAndReload(selectedLanguage) {
    await indicoAxios.post(changeLanguage(), {lang: selectedLanguage});
    location.reload();
}

export default function UserMenu({userData, staticData}) {
    if (!userData) {
        return '';
    }

    const {availableLanguages} = staticData;
    const {firstName, lastName, email, language, isAdmin, avatarBgColor} = userData;
    const avatar = (
        <Avatar style={{
            backgroundColor: avatarBgColor
        }}>
            {firstName[0]}
        </Avatar>
    );

    const languageSelector = (
        <ContainerBound>
            {(getPopupContainer) => (
                <Select defaultValue={language}
                        styleName="language-selector-combo"
                        onSelect={postAndReload}
                        getPopupContainer={getPopupContainer}>
                    {Object.entries(availableLanguages).map(([key, name]) => (
                        <Select.Option key={key} value={key}>{name}</Select.Option>
                    ))}
                </Select>
            )}
        </ContainerBound>
    );

    return (
        <ArrowDownMenu>
            <Slot name="avatar">
                {avatar}
            </Slot>
            <Slot>
                <ContainerDiv styleName="user-popup">
                    <h3>{`${firstName} ${lastName}`}</h3>
                    <h4>{email}</h4>
                    <div styleName="links">
                        <Divider type="horizontal" />
                        <a href={userDashboard()}>
                            <Translate>My Profile</Translate>
                        </a>
                        <a href={userPreferences()}>
                            <Translate>My Preferences</Translate>
                        </a>
                        <div styleName="language-selector-field">
                            <Icon type="global" styleName="language-icon" />
                            {languageSelector}
                        </div>
                        <Divider type="horizontal" />
                        {isAdmin && (
                            <a href="">
                                <Translate>Administration</Translate>
                            </a>
                        )}
                        <a href={authLogout()}>
                            <Translate>Logout</Translate>
                        </a>
                    </div>
                </ContainerDiv>
            </Slot>
        </ArrowDownMenu>
    );
}

UserMenu.propTypes = {
    userData: propTypes.shape({
        firstName: propTypes.string,
        lastName: propTypes.string,
        id: propTypes.number,
        language: propTypes.string,
        isAdmin: propTypes.bool,
        avatarBgColor: propTypes.string
    }).isRequired,
    staticData: propTypes.shape({
        availableLanguages: propTypes.object
    }).isRequired
};
