// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionFavoriteURL from 'indico-url:contributions.favorite_contributions_api';

import _ from 'lodash';
import React, {useMemo} from 'react';
import ReactDOM from 'react-dom';
import {Icon, Loader, Message} from 'semantic-ui-react';

import {useIndicoAxiosWithMutation} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {ContributionList} from './ContributionList';
import {Contribution, ContributionRecord} from './types';

import './MyTimetable.module.scss';

interface MyTimetableProps {
  eventId: number;
  timezone: string;
}

export function MyTimetable({eventId, timezone}: MyTimetableProps) {
  const {
    data: favoriteContributions,
    loading,
    mutate,
    mutating,
  } = useIndicoAxiosWithMutation<ContributionRecord>({
    url: contributionFavoriteURL({event_id: eventId}),
  });

  const sortedContributions = useMemo(() => {
    if (favoriteContributions === null) {
      return null;
    }
    return _.sortBy(Object.values(favoriteContributions), c => [
      c.start_dt === null,
      c.start_dt,
      c.friendly_id,
    ]);
  }, [favoriteContributions]);

  const removeScheduledContribution = async (id: number) => {
    try {
      await mutate(
        indicoAxios.delete(contributionFavoriteURL({contrib_id: id, event_id: eventId})),
        oldData => _.omit(oldData, id)
      );
    } catch (error) {
      handleAxiosError(error);
      return;
    }
  };

  if (loading) {
    return <Loader active size="massive" inline="centered" />;
  }

  if (favoriteContributions !== null && Object.keys(favoriteContributions).length === 0) {
    return (
      <Message info>
        <Translate>There are no contributions in your timetable.</Translate>
      </Message>
    );
  }

  return (
    <ContributionList
      timezone={timezone}
      contributions={sortedContributions}
      emptyText={Translate.string('You have not added any contributions to your timetable.')}
      actionsElement={(contribution: Contribution) => (
        <Icon
          styleName="delete-button"
          name="close"
          disabled={mutating}
          onClick={() => removeScheduledContribution(contribution.id)}
          link
        />
      )}
    />
  );
}

customElements.define(
  'ind-my-timetable',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <MyTimetable
          eventId={JSON.parse(this.getAttribute('event-id') ?? '')}
          timezone={this.getAttribute('timezone') ?? ''}
        />,
        this
      );
    }
  }
);
