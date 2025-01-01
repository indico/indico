// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {Favorite} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

document.addEventListener('DOMContentLoaded', () => {
  const favoriteContainer = document.querySelector('#favorite-link');

  if (!favoriteContainer) {
    return;
  }

  const eventId = favoriteContainer.dataset.eventId;
  const favorited = favoriteContainer.dataset.favorited !== undefined;

  ReactDOM.render(
    <Favorite
      type="event"
      id={eventId}
      favorited={favorited}
      setFavText={Translate.string('Add event to favorites')}
      deleteFavText={Translate.string('Delete event from favorites')}
    />,
    favoriteContainer
  );
});
