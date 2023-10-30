// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryFavoriteURL from 'indico-url:users.user_favorites_category_api';
import eventFavoriteURL from 'indico-url:users.user_favorites_event_api';

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

export default function Favorite({type, id, favorited, setFavText, deleteFavText}) {
  const [fav, setFav] = useState(favorited);

  const deleteFavorite = async favId => {
    try {
      if (type === 'category') {
        await indicoAxios.delete(categoryFavoriteURL({category_id: favId}));
      } else if (type === 'event') {
        await indicoAxios.delete(eventFavoriteURL({event_id: favId}));
      } else {
        throw new Error('No valid favorite button type given.');
      }
      setFav(false);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
  };

  const putFavorite = async favId => {
    try {
      if (type === 'category') {
        await indicoAxios.put(categoryFavoriteURL({category_id: favId}));
      } else if (type === 'event') {
        await indicoAxios.put(eventFavoriteURL({event_id: favId}));
      } else {
        throw new Error('No valid favorite button type given.');
      }
      setFav(true);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
  };

  return (
    <ind-with-tooltip>
      {fav ? (
        <button onClick={() => deleteFavorite(id)} data-favorited={fav} type="button">
          <span data-tip-content>{deleteFavText}</span>
        </button>
      ) : (
        <button onClick={() => putFavorite(id)} data-favorited={fav} type="button">
          <span data-tip-content>{setFavText}</span>
        </button>
      )}
    </ind-with-tooltip>
  );
}

Favorite.propTypes = {
  type: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  favorited: PropTypes.bool.isRequired,
  setFavText: PropTypes.string.isRequired,
  deleteFavText: PropTypes.string.isRequired,
};
