// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contributionFavoriteURL from 'indico-url:contributions.favorite_contributions_api';

import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';
import {Icon} from 'semantic-ui-react';

import {useIndicoAxiosWithMutation} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {ContributionList} from './ContributionList';
import {Contribution, ContributionRecord} from './types';

import './MyTimetable.module.scss';

interface MyTimetableProps {
  eventId: number;
}

export function MyTimetable({eventId}: MyTimetableProps) {
  const {
    data: scheduledContributions,
    loading,
    mutate,
    mutating,
  } = useIndicoAxiosWithMutation<ContributionRecord>({
    url: contributionFavoriteURL({event_id: eventId}),
  });

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

  return (
    <ContributionList
      loading={loading}
      contributions={scheduledContributions}
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
      ReactDOM.render(<MyTimetable eventId={JSON.parse(this.getAttribute('event-id'))} />, this);
    }
  }
);
