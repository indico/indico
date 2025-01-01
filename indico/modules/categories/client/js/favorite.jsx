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
  const favoriteContainer = document.querySelector('#fav-button');

  if (!favoriteContainer) {
    return;
  }

  const categoryId = favoriteContainer.dataset.categoryId;
  const favorited = favoriteContainer.dataset.favorited !== undefined;

  ReactDOM.render(
    <Favorite
      type="category"
      id={categoryId}
      favorited={favorited}
      setFavText={Translate.string(
        'Add category to favorites (This will make events in this category visible on your Dashboard.)'
      )}
      deleteFavText={Translate.string('Delete category from favorites.')}
    />,
    favoriteContainer
  );
});
