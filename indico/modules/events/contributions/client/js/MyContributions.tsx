// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import myContributionsURL from 'indico-url:contributions.my_contributions_api';

import React from 'react';
import ReactDOM from 'react-dom';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import {ContributionList} from './ContributionList';
import {FavoriteContributions} from './FavoriteContributions';
import {Contribution} from './types';

interface MyContributionsProps {
  eventId: number;
}

const SECTIONS = {
  speaker: Translate.string('Speaker'),
  author: Translate.string('Author'),
  'co-author': Translate.string('Co-author'),
  submitter: Translate.string('Submitter'),
};

function editContribution(contribution: Contribution) {
  if (contribution.edit_url) {
    return (
      <a
        href="#"
        className="icon-edit js-edit-contribution"
        title={Translate.string('Edit this contribution')}
        data-title={`${Translate.string('Edit contribution')} '${contribution.title}'`}
        data-href={contribution.edit_url}
        data-ajax-dialog
        data-reload-after
      />
    );
  }
  return null;
}

export function MyContributions({eventId}: MyContributionsProps) {
  const {loading, data: myContributions} = useIndicoAxios({
    url: myContributionsURL({event_id: eventId}),
  });

  return (
    <div>
      <FavoriteContributions eventId={eventId} />
      {Object.entries(SECTIONS).map(([section, title]) => (
        <ContributionList
          key={section}
          loading={loading}
          title={title}
          contributions={myContributions?.[section] ?? null}
          actionsElement={editContribution}
          hideWhenEmpty
        />
      ))}
    </div>
  );
}

customElements.define(
  'ind-my-contributions',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <MyContributions eventId={JSON.parse(this.getAttribute('event-id'))} />,
        this
      );
    }
  }
);
