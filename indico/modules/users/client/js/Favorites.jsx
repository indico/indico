// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryFavoriteURL from 'indico-url:users.user_favorites_category_api';

import _ from 'lodash';
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
  ReactDOM.render(<FavoriteManager userId={userId} />, document.getElementById('user-favorites'));
};

function FavoriteManager({userId}) {
  return (
    <>
      <FavoriteUserManager userId={userId} />
      <FavoriteCatManager userId={userId} />
    </>
  );
}

FavoriteManager.propTypes = {
  userId: PropTypes.number,
};

FavoriteManager.defaultProps = {
  userId: null,
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
            <Translate>Favourite Categories</Translate>
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
                        content={Translate.string('Remove from favourites')}
                        position="bottom center"
                      />
                    </div>
                  </List.Content>
                </List.Item>
              ))}
            </List>
          ) : (
            <div styleName="empty-favorites">
              <Translate>You have not marked any category as favourite.</Translate>
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

function FavoriteUserManager({userId}) {
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
            <Translate>Favourite Users</Translate>
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
                          onClick={() => deleteFavoriteUser(user.userId)}
                          link
                        />
                      }
                      content={Translate.string('Remove from favourites')}
                      position="bottom center"
                    />
                  </div>
                </List.Item>
              ))}
            </List>
          ) : (
            <div styleName="empty-favorites">
              <Translate>You have not marked any user as favourite.</Translate>
            </div>
          )}
        </div>
      </div>
      <UserSearch
        existing={Object.values(favoriteUsers).map(u => u.identifier)}
        onAddItems={e => e.forEach(u => addFavoriteUser(u.userId))}
        triggerFactory={searchTrigger}
      />
    </div>
  );
}

FavoriteUserManager.propTypes = {
  userId: PropTypes.number,
};

FavoriteUserManager.defaultProps = {
  userId: null,
};
