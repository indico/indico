// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiEventListURL from 'indico-url:categories.api_event_list';
import apiViewDataURL from 'indico-url:categories.api_view_data';

import React from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

import {Button} from '../button/Button';
import {TimelineItem} from '../timeline/Timeline';
import {YearPicker} from '../yearPicker/YearPicker';

import {ListItem} from './ListItem';

import './EventList.module.scss';

interface EventListProps {
  categoryId: number;
}
export function EventList({categoryId}: EventListProps) {
  const [selectedYear, setSelectedYear] = React.useState<number>(new Date().getFullYear());

  const viewDataURL = apiViewDataURL({
    category_id: String(categoryId),
  });
  const {data: viewData} = useIndicoAxios(viewDataURL, {
    camelize: true,
  });

  const {data: eventListData, loading: fetchingList} = useIndicoAxios(
    apiEventListURL({
      category_id: String(categoryId),
      year: String(selectedYear),
    }),
    {
      camelize: true,
    }
  );

  const activeData = eventListData ?? viewData;

  const [userFutureExpanded, setUserFutureExpanded] = React.useState<boolean | null>(null);
  const [userPastExpanded, setUserPastExpanded] = React.useState<boolean | null>(null);

  const futureEventsExpanded = userFutureExpanded ?? viewData?.showFutureEvents ?? false;
  const pastEventsExpanded = userPastExpanded ?? viewData?.showPastEvents ?? false;

  const futureEventsCount = activeData?.futureEventCount ?? 0;
  const pastEventsCount = activeData?.pastEventCount ?? 0;

  const events = React.useMemo(() => {
    if (!activeData) {
      return [];
    }

    const baseEvents = activeData.eventsByMonth ?? [];
    const futureEvents = futureEventsExpanded ? (activeData.futureEventsByMonth ?? []) : [];
    const pastEvents = pastEventsExpanded ? (activeData.pastEventsByMonth ?? []) : [];

    return [...futureEvents, ...baseEvents, ...pastEvents];
  }, [activeData, futureEventsExpanded, pastEventsExpanded]);

  if (!viewData) {
    return <div>Loading...</div>;
  }

  return (
    <div styleName="event-list">
      <YearPicker
        yearList={viewData.availableYears}
        selectedYear={selectedYear}
        onYearSelect={year => {
          setSelectedYear(year);
        }}
      />

      {futureEventsCount > 0 && (
        <Button
          styleName="event-list-show-more"
          variant="transparent"
          size="sm"
          disabled={fetchingList}
          icon={futureEventsExpanded ? 'fas:chevron-down' : 'fas:chevron-up'}
          iconPosition="right"
          onClick={() => setUserFutureExpanded(!futureEventsExpanded)}
        >
          {futureEventsExpanded
            ? Translate.string('Show less ({0})', [futureEventsCount])
            : Translate.string('Show more ({0})', [futureEventsCount])}
        </Button>
      )}

      {events.map(month => (
        <TimelineItem key={month.name} styleName="event-list-month">
          <TimelineItem.Title dotColor="primary">{month.name.split(' ')[0]}</TimelineItem.Title>
          <TimelineItem.Content>
            {month.events.map(event => (
              <ListItem styleName="event-list-item" key={event.id + month.name} href={event.url}>
                <div styleName="event-list-item-start-section">
                  <ListItem.Tag
                    icon="fas:calendar"
                    color="primary"
                    variant="light"
                    size="sm"
                    textWeight="regular"
                    styleName="event-list-item-date-time-tag"
                  >
                    {event.date}
                  </ListItem.Tag>
                  <div styleName="event-list-item-header-label-section">
                    <div styleName="event-list-item-header-section">
                      <ListItem.Header>{event.verbosedTitle}</ListItem.Header>
                      {event.isFavorite && (
                        <ListItem.Icon
                          title={Translate.string('You have favorited this event.')}
                          icon="fas:star"
                          color="warning"
                          variant="compact"
                          size="xs"
                          styleName="event-list-item-favorite-icon"
                        />
                      )}
                      {event.seriesLabel && (
                        <ListItem.Details styleName="event-list-item-series-label">
                          {event.seriesLabel}
                        </ListItem.Details>
                      )}
                    </div>
                    {event.label && (
                      <ListItem.Tag color={event.labelColor} icon="fas:tag" size="xs">
                        {event.label}
                      </ListItem.Tag>
                    )}
                  </div>
                </div>
                <div styleName="event-list-item-tag-section">
                  {event.isRecent && (
                    <ListItem.Tag
                      title={Translate.string('New')}
                      color="primary"
                      variant="light"
                      size="xs"
                    >
                      New
                    </ListItem.Tag>
                  )}
                  {event.visibility === 0 && (
                    <ListItem.Tag
                      title={Translate.string('This event is hidden')}
                      color="gray"
                      variant="light"
                      size="xs"
                    >
                      Hidden
                    </ListItem.Tag>
                  )}
                  {event.isHappeningNow && (
                    <ListItem.Tag
                      title={Translate.string('Ongoing')}
                      color="warning"
                      variant="light"
                      size="xs"
                    >
                      Ongoing
                    </ListItem.Tag>
                  )}

                  {event.isProtected && (
                    <ListItem.Icon
                      icon="fas:shield-halved"
                      color="error"
                      size="xs"
                      variant="light"
                      ariaLabel="Protected Category"
                      title={Translate.string('Protected')}
                    />
                  )}
                </div>
              </ListItem>
            ))}
          </TimelineItem.Content>
        </TimelineItem>
      ))}

      {pastEventsCount > 0 && (
        <Button
          styleName="event-list-show-more"
          variant="transparent"
          color="primary"
          size="sm"
          disabled={fetchingList}
          icon={pastEventsExpanded ? 'fas:chevron-up' : 'fas:chevron-down'}
          iconPosition="right"
          onClick={() => setUserPastExpanded(!pastEventsExpanded)}
        >
          {pastEventsExpanded
            ? Translate.string('Show less ({0})', [pastEventsCount])
            : Translate.string('Show more ({0})', [pastEventsCount])}
        </Button>
      )}
    </div>
  );
}
