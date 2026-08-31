// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoryFavoriteURL from 'indico-url:users.user_favorites_category_api';
import eventFavoriteURL from 'indico-url:users.user_favorites_event_api';

import React from 'react';

import {Button, ButtonSize} from 'indico/NGUI/button/Button';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

interface FavoriteButtonProps {
  type: 'event' | 'category';
  id: number | string;
  favorited: boolean;
  className?: string;
  size?: ButtonSize;
}

export function FavoriteButton({type, id, favorited, className, size = 'lg'}: FavoriteButtonProps) {
  const [isFavorite, setIsFavorite] = React.useState(favorited);
  const [submitting, setSubmitting] = React.useState(false);

  React.useEffect(() => {
    setIsFavorite(favorited);
  }, [favorited]);

  const toggleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (submitting) {
      return;
    }

    const url =
      type === 'event' ? eventFavoriteURL({event_id: id}) : categoryFavoriteURL({category_id: id});

    setSubmitting(true);
    try {
      if (isFavorite) {
        await indicoAxios.delete(url);
      } else {
        await indicoAxios.put(url);
      }
      setIsFavorite(!isFavorite);
    } catch (error) {
      handleAxiosError(error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Button
      icon={isFavorite ? 'fas:star' : 'far:star'}
      color="warning"
      variant="transparent"
      size={size}
      onClick={toggleFavorite}
      disabled={submitting}
      aria-pressed={isFavorite}
      iconOnly
      squared
      aria-label={
        isFavorite
          ? Translate.string('Unfavorite this event')
          : Translate.string('Favorite this event')
      }
      className={className}
    />
  );
}
