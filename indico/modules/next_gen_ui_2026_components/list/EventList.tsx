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

import {TimelineItem} from '../timeline/Timeline';

import {ListItem} from './ListItem';

import './EventList.module.scss';

interface EventListProps {
  categoryId: number;
}

export function EventList({categoryId}: EventListProps) {
  const viewDataURL = apiViewDataURL({
    category_id: String(categoryId),
  });

  const eventListURL = apiEventListURL({
    category_id: String(categoryId),
    after: '2025-05',
  });

  const {data: viewData} = useIndicoAxios(viewDataURL, {
    camelize: true,
  });

  const {data: eventListData} = useIndicoAxios(eventListURL, {
    camelize: true,
  });

  if (!viewData || !eventListData) {
    return <div>Loading...</div>;
  }

  const events = eventListData.eventsByYear ?? [];

  return (
    <div>
      <h3>Event list:</h3>

      {events.map(year => (
        <div key={year.year}>
          {/* <h4>{year.year}</h4> */}
          {year.months.map(month => (
            <TimelineItem key={month.name}>
              <TimelineItem.Title dotColor="primary">{month.name}</TimelineItem.Title>
              <TimelineItem.Content>
                {month.events.map(event => (
                  <ListItem
                    styleName="event-list-item"
                    key={event.id + month.name}
                    href={event.url}
                  >
                    <div styleName="event-list-item-start-section">
                      <ListItem.Tag
                        icon="fas:calendar"
                        color="primary"
                        variant="light"
                        size="sm"
                        textWeight="medium"
                        styleName="event-list-item-date-time-tag"
                      >
                        {event.date}
                      </ListItem.Tag>
                      <ListItem.Header styleName="event-list-item-header">
                        {event.verbosedTitle}
                      </ListItem.Header>
                      {event.isFavorite && (
                        <ListItem.Icon
                          title={Translate.string('You have favorited this event.')}
                          icon="fas:star"
                          color="warning"
                          variant="compact"
                          size="xxs"
                          styleName="event-list-item-favorite-icon"
                        />
                      )}
                      {event.seriesLabel && (
                        <ListItem.Details styleName="event-list-item-series-label">
                          {event.seriesLabel}
                        </ListItem.Details>
                      )}
                    </div>
                    <div styleName="event-list-item-tag-section">
                      {event.label && (
                        <ListItem.Tag
                          title={Translate.string('Event label')}
                          color={event.labelColor}
                          variant="transparent"
                          outlined
                          size="xs"
                          styleName="event-list-item-label-tag"
                        >
                          {event.label}
                        </ListItem.Tag>
                      )}
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
        </div>
      ))}
    </div>
  );
}
