// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import authLogout from 'indico-url:auth.logout';
import adminDashboard from 'indico-url:core.admin_dashboard';
import changeLanguage from 'indico-url:core.change_lang';
import userDashboard from 'indico-url:users.user_dashboard';
import userPreferences from 'indico-url:users.user_preferences';

import PropTypes from 'prop-types';
import qs from 'qs';
import React from 'react';
import {Dropdown, Icon, Image} from 'semantic-ui-react';

import {impersonateUser} from 'indico/modules/core/impersonation';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {useFavoriteUsers} from '../hooks';

import {UserSearch} from './principals/Search';

async function postAndReload(selectedLanguage) {
  try {
    await indicoAxios.post(changeLanguage(), qs.stringify({lang: selectedLanguage}));
  } catch (error) {
    handleAxiosError(error);
    return;
  }
  location.reload();
}

function UserImpersonation() {
  const [favoriteUsers] = useFavoriteUsers();

  return (
    <UserSearch
      triggerFactory={({disabled, onClick}) => (
        <Dropdown.Item onClick={onClick} disabled={disabled}>
          <Translate>Impersonate user</Translate>
        </Dropdown.Item>
      )}
      existing={[]}
      onAddItems={({userId}) => impersonateUser(userId)}
      favorites={favoriteUsers}
      withExternalUsers={false}
      single
      alwaysConfirm
    />
  );
}

export default function UserMenu({userData, languages, hasLoadedConfig, hasLoadedUserInfo}) {
  if (!userData || !languages || !hasLoadedConfig || !hasLoadedUserInfo) {
    return '';
  }

  const {firstName, lastName, email, language, isAdmin, avatarURL} = userData;
  const avatar = <Image avatar src={avatarURL} size="mini" />;

  const languageSelector = trigger => {
    return (
      <Dropdown
        floating
        trigger={trigger}
        value={language}
        selectOnBlur={false}
        onChange={(_, {value}) => {
          if (value !== language) {
            postAndReload(value);
          }
        }}
        options={Object.entries(languages).map(([key, [name, territory]]) => ({
          key,
          text: territory ? `${name} (${territory})` : name,
          value: key,
        }))}
      />
    );
  };

  const headerContent = (
    <div>
      {firstName} {lastName}
      <br />
      {email}
    </div>
  );

  const langInfo = languages[language] || [language, null];
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
          {languageSelector(
            <>
              <Icon name="globe" /> {langInfo[1] ? `${langInfo[0]} (${langInfo[1]})` : langInfo[0]}
            </>
          )}
        </Dropdown.Header>
        <Dropdown.Divider />
        {isAdmin && (
          <>
            <Dropdown.Item as="a" href={adminDashboard()}>
              <Translate>Administration</Translate>
            </Dropdown.Item>
            <UserImpersonation />
          </>
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
    email: PropTypes.string,
    id: PropTypes.number,
    language: PropTypes.string,
    isAdmin: PropTypes.bool,
    avatarURL: PropTypes.string,
  }).isRequired,
  languages: PropTypes.object.isRequired,
  hasLoadedConfig: PropTypes.bool.isRequired,
  hasLoadedUserInfo: PropTypes.bool.isRequired,
};
