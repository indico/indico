// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import myContributionsURL from 'indico-url:contributions.my_contributions_api';

import React from 'react';
import ReactDOM from 'react-dom';
import {Loader, Message} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import {ContributionList} from './ContributionList';
import {Contribution} from './types';

import './MyContributions.module.scss';

interface MyContributionsProps {
  eventId: number;
}

const SECTIONS = {
  speaker: Translate.string('Speaker'),
  primary: Translate.string('Author'),
  secondary: Translate.string('Co-author'),
  submitter: Translate.string('Submitter'),
};

function editContribution(contribution: Contribution) {
  if (contribution.edit_url) {
    return (
      <a
        href="#"
        styleName="edit-button"
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

  if (loading) {
    return <Loader active size="massive" inline="centered" />;
  }

  if (myContributions !== null && Object.keys(myContributions).length === 0) {
    return (
      <Message info>
        <Translate>There are no contributions linked to your Indico profile.</Translate>
      </Message>
    );
  }

  return (
    <>
      {Object.entries(SECTIONS).map(([section, title]) => (
        <ContributionList
          key={section}
          title={title}
          contributions={myContributions?.[section] ?? null}
          actionsElement={editContribution}
        />
      ))}
    </>
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
