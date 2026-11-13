// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import authLogout from 'indico-url:auth.logout';
import adminDashboard from 'indico-url:core.admin_dashboard';
import changeLanguage from 'indico-url:core.change_lang';
import userDashboard from 'indico-url:users.user_dashboard';
import userPreferences from 'indico-url:users.user_preferences';

import _ from 'lodash';
import PropTypes from 'prop-types';
import qs from 'qs';
import React, {useCallback, useEffect, useLayoutEffect, useRef, useState} from 'react';
import {Icon, Image} from 'semantic-ui-react';

import {impersonateUser} from 'indico/modules/core/impersonation';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {useFavoriteUsers} from '../hooks';

import {UserSearch} from './principals/Search';

import styles from './UserMenu.module.scss';

async function postAndReload(selectedLanguage) {
  try {
    await indicoAxios.post(changeLanguage(), qs.stringify({lang: selectedLanguage}));
  } catch (error) {
    handleAxiosError(error);
    return;
  }
  location.reload();
}

function UserImpersonation({onOpen, onClose}) {
  const [favoriteError, setFavoriteError] = useState(null);
  const handleFavoriteError = useCallback(() => {
    setFavoriteError(
      Translate.string('Favorites could not be loaded or updated. Please try again.')
    );
  }, []);
  const [favorites, [add, remove, load], loading] = useFavoriteUsers(
    null,
    false,
    handleFavoriteError
  );
  const runFavoriteAction = action => async identifier => {
    setFavoriteError(null);
    await action(identifier);
  };
  const favoriteUsersController = [
    favorites,
    [runFavoriteAction(add), runFavoriteAction(remove), load],
    loading,
  ];

  return (
    <UserSearch
      triggerFactory={({disabled, onClick}) => (
        <button type="button" onClick={onClick} disabled={disabled}>
          <Translate>Impersonate user</Translate>
        </button>
      )}
      existing={[]}
      onAddItems={({userId}) => impersonateUser(userId)}
      favoritesController={favoriteUsersController}
      withExternalUsers={false}
      single
      alwaysConfirm
      nativeModal
      errorMessage={favoriteError}
      onOpen={onOpen}
      onClose={() => {
        setFavoriteError(null);
        onClose();
      }}
    />
  );
}

UserImpersonation.propTypes = {
  onOpen: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

/** Account navigation and language choices shared by room-booking pages. */
export default function UserMenu({userData, languages, hasLoadedConfig, hasLoadedUserInfo}) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const triggerRef = useRef(null);
  const panelRef = useRef(null);
  const impersonatingRef = useRef(false);

  useLayoutEffect(() => {
    if (!open) {
      return undefined;
    }
    const panel = panelRef.current;
    const updateOrigin = () => {
      const {top, left} = panel.getBoundingClientRect();
      panel.style.setProperty('--panel-top', `${top + panel.clientTop}px`);
      panel.style.setProperty('--panel-left', `${left + panel.clientLeft}px`);
    };
    updateOrigin();
    const observer = new ResizeObserver(updateOrigin);
    observer.observe(panel);
    window.addEventListener('resize', updateOrigin);
    window.addEventListener('scroll', updateOrigin);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateOrigin);
      window.removeEventListener('scroll', updateOrigin);
    };
  }, [open]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }
    const handlePointerDown = event => {
      if (
        !impersonatingRef.current &&
        !menuRef.current?.contains(event.target) &&
        !event.target.closest('.account-impersonation')
      ) {
        setOpen(false);
      }
    };
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [open]);

  if (!userData || !languages || !hasLoadedConfig || !hasLoadedUserInfo) {
    return '';
  }

  const {firstName, lastName, email, language, isAdmin, avatarURL} = userData;
  const [langName, langTerritory] = languages[language] || [language, null, false];
  const languageName = langTerritory ? `${langName} (${langTerritory})` : langName;

  const handleKeyDown = event => {
    if (event.key === 'Escape' && open && !event.defaultPrevented) {
      event.preventDefault();
      event.stopPropagation();
      setOpen(false);
      triggerRef.current.focus();
    } else if (
      event.target === triggerRef.current &&
      ['ArrowDown', 'ArrowUp'].includes(event.key)
    ) {
      event.preventDefault();
      setOpen(true);
      requestAnimationFrame(() => {
        const destinations = menuRef.current.querySelectorAll('menu > li > a, menu > li > button');
        const index = event.key === 'ArrowUp' ? destinations.length - 1 : 0;
        destinations[index]?.focus();
      });
    }
  };

  return (
    <div
      ref={menuRef}
      styleName="account-menu"
      onKeyDown={handleKeyDown}
      onBlur={() => {
        requestAnimationFrame(() => {
          const active = document.activeElement;
          if (
            !impersonatingRef.current &&
            !menuRef.current?.contains(active) &&
            !active?.closest('.account-impersonation')
          ) {
            setOpen(false);
          }
        });
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        className="account-menu-trigger"
        styleName="trigger"
        aria-expanded={open}
        onClick={() => setOpen(value => !value)}
      >
        <Image avatar src={avatarURL} size="mini" alt="" />
        <span styleName="visually-hidden">
          {Translate.string('Account menu for {name}', {name: `${firstName} ${lastName}`})}
        </span>
        <Icon name="dropdown" />
      </button>
      <div ref={panelRef} styleName="panel" hidden={!open}>
        <div styleName="panel-content">
          <div styleName="identity">
            <div>
              {firstName} {lastName}
              <br />
              {email}
            </div>
          </div>
          <menu
            onFocus={event => {
              if (
                event.currentTarget.contains(event.target) &&
                !event.target.closest('ind-menu > menu')
              ) {
                event.target.scrollIntoView({block: 'nearest', inline: 'nearest'});
              }
            }}
          >
            <li>
              <a href={userDashboard()}>
                <Translate>My Profile</Translate>
              </a>
            </li>
            <li>
              <a href={userPreferences()}>
                <Translate>My Preferences</Translate>
              </a>
            </li>
            <li styleName="language-header">
              <ind-menu
                class={styles.languages}
                onKeyDownCapture={event => {
                  if (event.key === 'Escape' && event.currentTarget.hasAttribute('open')) {
                    event.preventDefault();
                  }
                }}
              >
                <button type="button" className="account-language-trigger">
                  <Icon name="globe" />{' '}
                  <span styleName="visually-hidden">
                    <Translate>Change language:</Translate>{' '}
                  </span>
                  {languageName}
                  <Icon name="dropdown" styleName="language-caret" />
                </button>
                <menu
                  hidden
                  onFocus={event => {
                    const menu = event.currentTarget;
                    const choice = event.target;
                    requestAnimationFrame(() => {
                      const bounds = menu.getBoundingClientRect();
                      const item = choice.getBoundingClientRect();
                      if (item.bottom > bounds.bottom) {
                        menu.scrollTop += item.bottom - bounds.bottom + menu.clientTop;
                      } else if (item.top < bounds.top) {
                        menu.scrollTop += item.top - bounds.top - menu.clientTop;
                      }
                    });
                  }}
                >
                  {_.sortBy(Object.entries(languages), x => x[1][0]).map(
                    ([key, [name, territory]]) => (
                      <li key={key}>
                        <button
                          type="button"
                          onClick={() => {
                            if (key !== language) {
                              postAndReload(key);
                            }
                          }}
                        >
                          <span styleName={key === language ? 'current-language' : undefined}>
                            {territory ? `${name} (${territory})` : name}
                          </span>
                          {key === language && (
                            <span styleName="visually-hidden">
                              {' '}
                              (<Translate>current</Translate>)
                            </span>
                          )}
                        </button>
                      </li>
                    )
                  )}
                </menu>
              </ind-menu>
            </li>
            {isAdmin && (
              <>
                <li>
                  <a href={adminDashboard()}>
                    <Translate>Administration</Translate>
                  </a>
                </li>
                <li>
                  <UserImpersonation
                    onOpen={() => {
                      impersonatingRef.current = true;
                    }}
                    onClose={() => {
                      impersonatingRef.current = false;
                    }}
                  />
                </li>
              </>
            )}
            <li>
              <a href={authLogout()}>
                <Translate>Logout</Translate>
              </a>
            </li>
          </menu>
        </div>
      </div>
    </div>
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
