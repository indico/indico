// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryFavoriteURL from 'indico-url:users.user_favorites_category_api';
import eventFavoriteURL from 'indico-url:users.user_favorites_event_api';

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useEffect, useState, useCallback} from 'react';
import ReactDOM from 'react-dom';
import {Button, Icon, List, Loader, Popup} from 'semantic-ui-react';

import {TooltipIfTruncated} from 'indico/react/components';
import {UserSearch} from 'indico/react/components/principals/Search';
import {useFavoriteUsers} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import './Favorites.module.scss';

window.setupFavoriteSelection = function setupFavoriteSelection(userId) {
  const container = document.getElementById('user-favorites');
  ReactDOM.render(
    <FavoriteManager userId={userId} searchToken={container.dataset.searchToken || null} />,
    container
  );
};

function FavoriteManager({userId, searchToken}) {
  return (
    <>
      <div className="row">
        <FavoriteUserManager userId={userId} searchToken={searchToken} />
        <FavoriteCatManager userId={userId} />
      </div>
      <div className="row">
        <FavoriteEventManager userId={userId} />
      </div>
    </>
  );
}

FavoriteManager.propTypes = {
  userId: PropTypes.number,
  searchToken: PropTypes.string,
};

FavoriteManager.defaultProps = {
  userId: null,
  searchToken: null,
};

function FavoriteCatManager({userId}) {
  const [favoriteCats, setFavoriteCats] = useState(null);
  const [loading, setLoading] = useState(true);

  const getFavoriteCats = useCallback(async () => {
    let res;
    try {
      res = await indicoAxios.get(categoryFavoriteURL(userId !== null ? {user_id: userId} : {}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setFavoriteCats(res.data);
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    getFavoriteCats();
  }, [getFavoriteCats]);

  const deleteFavoriteCat = async id => {
    try {
      await indicoAxios.delete(categoryFavoriteURL({category_id: id}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setFavoriteCats(values => _.omit(values, id));
  };
  return (
    <div className="column col-50">
      <div className="i-box just-group-list">
        <div className="i-box-header">
          <div className="i-box-title">
            <Translate>Favorite Categories</Translate>
          </div>
        </div>
        <div className="i-box-content">
          {loading ? (
            <Loader active inline styleName="fav-loader" />
          ) : favoriteCats !== null && Object.keys(favoriteCats).length > 0 ? (
            <List celled styleName="fav-list">
              {Object.values(favoriteCats).map(cat => (
                <List.Item key={cat.id} styleName="fav-item">
                  <List.Content>
                    <div styleName="list-flex">
                      <div>
                        <a href={cat.url} target="_blank" rel="noopener noreferrer">
                          {cat.title}
                        </a>
                        <br />
                        <TooltipIfTruncated>
                          <span styleName="detail">
                            {cat.chain_titles.slice(0, -1).join(' » ')}
                          </span>
                        </TooltipIfTruncated>
                      </div>
                      <Popup
                        trigger={
                          <Icon
                            styleName="delete-button"
                            name="close"
                            onClick={() => deleteFavoriteCat(cat.id)}
                            link
                          />
                        }
                        content={Translate.string('Remove from favorites')}
                        position="bottom center"
                      />
                    </div>
                  </List.Content>
                </List.Item>
              ))}
            </List>
          ) : (
            <div styleName="empty-favorites">
              <Translate>You have not marked any category as favorite.</Translate>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

FavoriteCatManager.propTypes = {
  userId: PropTypes.number,
};

FavoriteCatManager.defaultProps = {
  userId: null,
};

function FavoriteEventManager({userId}) {
  const [favoriteEvents, setFavoriteEvents] = useState(null);
  const [loading, setLoading] = useState(true);

  const getFavoriteEvents = useCallback(async () => {
    let res;
    try {
      res = await indicoAxios.get(eventFavoriteURL(userId !== null ? {user_id: userId} : {}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setFavoriteEvents(res.data);
    setLoading(false);
  }, [userId]);

  useEffect(() => {
    getFavoriteEvents();
  }, [getFavoriteEvents]);

  const deleteFavoriteEvent = async id => {
    try {
      await indicoAxios.delete(eventFavoriteURL({event_id: id}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setFavoriteEvents(values => _.omit(values, id));
  };

  return (
    <div styleName="favorite-event-container">
      <div className="i-box just-group-list">
        <div className="i-box-header">
          <div className="i-box-title">
            <Translate>Favorite Events</Translate>
          </div>
        </div>
        <div className="i-box-content">
          {loading ? (
            <Loader active inline styleName="fav-loader" />
          ) : favoriteEvents !== null && Object.keys(favoriteEvents).length > 0 ? (
            <List celled styleName="fav-list">
              {Object.values(favoriteEvents)
                .sort((a, b) => moment(b.start_dt) - moment(a.start_dt))
                .map(event => (
                  <List.Item key={event.url} styleName="fav-item">
                    <List.Content>
                      <div styleName="list-flex">
                        <span styleName="date-span">
                          {moment(event.start_dt).format('D MMM YYYY')}
                        </span>
                        <span styleName="event-name-box">
                          <a href={event.url} target="_blank" rel="noopener noreferrer">
                            {event.title}
                          </a>
                          <span dangerouslySetInnerHTML={{__html: event.label_markup}} />
                          <br />
                          <TooltipIfTruncated>
                            <span styleName="detail">
                              {event.chain_titles ? (
                                event.chain_titles.join(' » ')
                              ) : (
                                <Translate>Unlisted</Translate>
                              )}
                            </span>
                          </TooltipIfTruncated>
                        </span>
                        <Popup
                          trigger={
                            <Icon
                              styleName="delete-button"
                              name="close"
                              onClick={() => deleteFavoriteEvent(event.id)}
                              link
                            />
                          }
                          content={Translate.string('Remove from favorites')}
                          position="bottom center"
                        />
                      </div>
                    </List.Content>
                  </List.Item>
                ))}
            </List>
          ) : (
            <div styleName="empty-favorites">
              <Translate>You have not marked any event as favorite.</Translate>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

FavoriteEventManager.propTypes = {
  userId: PropTypes.number,
};

FavoriteEventManager.defaultProps = {
  userId: null,
};

function FavoriteUserManager({userId, searchToken}) {
  const [favoriteUsers, [addFavoriteUser, deleteFavoriteUser], loading] = useFavoriteUsers(userId);

  const searchTrigger = triggerProps => (
    <Button {...triggerProps} styleName="submit-button">
      <Translate>Add Indico user</Translate>
    </Button>
  );
  return (
    <div className="column col-50">
      <div className="i-box just-group-list">
        <div className="i-box-header">
          <div className="i-box-title">
            <Translate>Favorite Users</Translate>
          </div>
        </div>
        <div className="i-box-content">
          {loading ? (
            <Loader active inline styleName="fav-loader" />
          ) : favoriteUsers !== null && Object.keys(favoriteUsers).length > 0 ? (
            <List celled styleName="fav-list">
              {Object.values(_.orderBy(favoriteUsers, ['name'])).map(user => (
                <List.Item key={user.identifier} styleName="fav-item">
                  <div styleName="list-flex">
                    <div>
                      <span>{user.name}</span>
                      <br />
                      <TooltipIfTruncated>
                        <span styleName="detail">{user.detail}</span>
                      </TooltipIfTruncated>
                    </div>
                    <Popup
                      trigger={
                        <Icon
                          styleName="delete-button"
                          name="close"
                          onClick={() => deleteFavoriteUser(user.identifier)}
                          link
                        />
                      }
                      content={Translate.string('Remove from favorites')}
                      position="bottom center"
                    />
                  </div>
                </List.Item>
              ))}
            </List>
          ) : (
            <div styleName="empty-favorites">
              <Translate>You have not marked any user as favorite.</Translate>
            </div>
          )}
        </div>
      </div>
      {searchToken && (
        <UserSearch
          existing={Object.values(favoriteUsers).map(u => u.identifier)}
          onAddItems={e => e.forEach(u => addFavoriteUser(u.identifier))}
          triggerFactory={searchTrigger}
          searchToken={searchToken}
        />
      )}
    </div>
  );
}

FavoriteUserManager.propTypes = {
  userId: PropTypes.number,
  searchToken: PropTypes.string,
};

FavoriteUserManager.defaultProps = {
  userId: null,
  searchToken: null,
};
