// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionFavoriteURL from 'indico-url:users.user_favorites_contribution_api';

import _ from 'lodash';
import React, {useCallback, useEffect, useState} from 'react';
import {Icon, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {ContributionList} from './ContributionList';
import {Contribution, ContributionRecord} from './types';

import './FavoriteContributions.module.scss';

interface FavoriteContributionsProps {
  eventId: number;
}

export function FavoriteContributions({eventId}: FavoriteContributionsProps) {
  const [favoriteContributions, setFavoriteContributions] = useState<ContributionRecord | null>(
    null
  );
  const [loading, setLoading] = useState(true);

  const getFavoriteContributions = useCallback(async () => {
    try {
      const res = await indicoAxios.get(
        contributionFavoriteURL(eventId !== undefined ? {event_id: eventId} : {})
      );
      setFavoriteContributions(res.data);
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setLoading(false);
  }, [eventId]);

  useEffect(() => {
    getFavoriteContributions();
  }, [getFavoriteContributions]);

  const deleteFavoriteContribution = async (id: number) => {
    try {
      await indicoAxios.delete(contributionFavoriteURL({contrib_id: id}));
    } catch (error) {
      handleAxiosError(error);
      return;
    }
    setFavoriteContributions(values => _.omit(values, id));
  };

  return (
    <ContributionList
      title={Translate.string('Favorites')}
      loading={loading}
      contributions={favoriteContributions}
      emptyText={Translate.string('You have not marked any contribution as favorite.')}
      actionsElement={(contribution: Contribution) => (
        <Popup
          trigger={
            <Icon
              styleName="delete-button"
              name="close"
              onClick={() => deleteFavoriteContribution(contribution.id)}
              link
            />
          }
          content={Translate.string('Remove from favorites')}
          position="bottom center"
        />
      )}
    />
  );
}
