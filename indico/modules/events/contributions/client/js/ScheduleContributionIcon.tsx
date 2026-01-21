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
import {Translate} from 'indico/react/i18n';

interface ScheduleContributionIconProps {
  contributionId: number;
  eventId: number;
}

export default function ScheduleContributionIcon({
  contributionId,
  eventId,
}: ScheduleContributionIconProps) {
  const [scheduled, toggleScheduled, loading, saving] = useTogglableValue(
    contributionURL({contrib_id: contributionId, event_id: eventId})
  );

  return (
    <button
      type="button"
      disabled={saving || loading}
      className={`i-button icon-calendar-${scheduled ? 'check' : 'plus'}-o ${scheduled ? 'highlight' : ''}`}
      onClick={saving || loading ? undefined : toggleScheduled}
      data-title
      title={
        scheduled
          ? Translate.string('This contribution has been added to your timetable. Click to remove.')
          : Translate.string('Add this contribution to your timetable.')
      }
    />
  );
}

customElements.define(
  'ind-favorite-contribution-icon',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <ScheduleContributionIcon
          contributionId={JSON.parse(this.getAttribute('contribution-id'))}
          eventId={JSON.parse(this.getAttribute('event-id'))}
        />,
        this
      );
    }
  }
);
