// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryFavoriteURL from 'indico-url:users.user_favorites_category_api';
import eventFavoriteURL from 'indico-url:users.user_favorites_event_api';

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {IButton} from 'indico/react/components';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import Palette from 'indico/utils/palette';

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

  return fav ? (
    <IButton
      icon="star"
      classes={type === 'event' ? {'height-full': true, 'text-color': true, subtle: true} : {}}
      style={type === 'event' ? {color: Palette.indicoBlue} : {}}
      highlight
      title={deleteFavText}
      onClick={() => deleteFavorite(id)}
    />
  ) : (
    <IButton
      icon="star-empty"
      classes={type === 'event' ? {'height-full': true, 'text-color': true, subtle: true} : {}}
      title={setFavText}
      onClick={() => putFavorite(id)}
    />
  );
}

Favorite.propTypes = {
  type: PropTypes.string.isRequired,
  id: PropTypes.string.isRequired,
  favorited: PropTypes.bool.isRequired,
  setFavText: PropTypes.string.isRequired,
  deleteFavText: PropTypes.string.isRequired,
};
