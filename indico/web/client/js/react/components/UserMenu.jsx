// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import qs from 'qs';
import React from 'react';
import PropTypes from 'prop-types';
import {Dropdown, Icon, Label} from 'semantic-ui-react';

import userDashboard from 'indico-url:users.user_dashboard';
import userPreferences from 'indico-url:users.user_preferences';
import authLogout from 'indico-url:auth.logout';
import adminDashboard from 'indico-url:core.admin_dashboard';
import changeLanguage from 'indico-url:core.change_lang';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './UserMenu.module.scss';


async function postAndReload(selectedLanguage) {
    try {
        await indicoAxios.post(changeLanguage(), qs.stringify({lang: selectedLanguage}));
    } catch (error) {
        handleAxiosError(error);
        return;
    }
    location.reload();
}

export default function UserMenu({userData, languages}) {
    if (!userData) {
        return '';
    }

    const {firstName, lastName, email, language, isAdmin, avatarBgColor} = userData;
    const avatar = (
        <Label circular size="large" style={{
            backgroundColor: avatarBgColor
        }} styleName="user-menu-avatar">
            {firstName[0]}
        </Label>
    );

    const languageSelector = (
        <Dropdown value={language}
                  selectOnBlur={false}
                  onChange={(_, {value}) => {
                      if (value !== language) {
                          postAndReload(value);
                      }
                  }}
                  options={Object.entries(languages).map(([key, name]) => ({
                      key, text: name, value: key
                  }))} />
    );

    const headerContent = (
        <div>
            {firstName} {lastName}
            <br />
            {email}
        </div>
    );

    return (
        <Dropdown trigger={avatar} pointing="top right">
            <Dropdown.Menu>
                <Dropdown.Header content={headerContent} />
                <Dropdown.Divider />
                <Dropdown.Item as="a" href={userDashboard()}>
                    <Translate>My Profile</Translate>
                </Dropdown.Item>
                <Dropdown.Item as="a" href={userPreferences()}>
                    <Translate>My Preferences</Translate>
                </Dropdown.Item>
                <Dropdown.Header>
                    <Icon name="globe" />
                    {languageSelector}
                </Dropdown.Header>
                <Dropdown.Divider />
                {isAdmin && (
                    <Dropdown.Item as="a" href={adminDashboard()}>
                        <Translate>Administration</Translate>
                    </Dropdown.Item>
                )}
                <Dropdown.Item as="a" href={authLogout()}>
                    <Translate>Logout</Translate>
                </Dropdown.Item>
            </Dropdown.Menu>
        </Dropdown>
    );
}

UserMenu.propTypes = {
    userData: PropTypes.shape({
        firstName: PropTypes.string,
        lastName: PropTypes.string,
        id: PropTypes.number,
        language: PropTypes.string,
        isAdmin: PropTypes.bool,
        avatarBgColor: PropTypes.string
    }).isRequired,
    languages: PropTypes.object.isRequired,
};
