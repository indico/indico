// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionURL from 'indico-url:contributions.favorite_contributions_api';

import React from 'react';
import ReactDOM from 'react-dom';

import {useTogglableValue} from 'indico/react/hooks';

import './FavoriteContributionIcon.module.scss';

interface FavoriteContributionIconProps {
  contributionId: number;
  eventId: number;
}

export default function FavoriteContributionIcon({
  contributionId,
  eventId,
}: FavoriteContributionIconProps) {
  const [favorited, toggleFavorite, loading, saving] = useTogglableValue(
    contributionURL({contrib_id: contributionId, event_id: eventId})
  );

  return (
    <i
      styleName={`toggle-button ${loading ? 'hidden' : saving ? '' : 'clickable'}`}
      className={`icon-star${favorited ? '' : '-empty'}`}
      onClick={saving || loading ? undefined : toggleFavorite}
    />
  );
}

customElements.define(
  'ind-favorite-contribution-icon',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <FavoriteContributionIcon
          contributionId={JSON.parse(this.getAttribute('contribution-id'))}
          eventId={JSON.parse(this.getAttribute('event-id'))}
        />,
        this
      );
    }
  }
);
