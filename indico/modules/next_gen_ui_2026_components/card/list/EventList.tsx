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
        <div key={year.year} role="group">
          {/* <h4>{year.year}</h4> */}
          {year.months.map(month => (
            <div key={month.name} role="group">
              <h5>
                <span styleName="dot" />
                {month.name.split(' ')[0]}
              </h5>
              <div styleName="month-events-wrapper">
                <div styleName="line" />

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
                      >
                        {event.date}
                      </ListItem.Tag>

                      <ListItem.Header>{event.title}</ListItem.Header>
                    </div>
                    <div styleName="event-list-item-tag-section">
                      {event.isRecent && (
                        <ListItem.Tag color="primary" variant="light" size="xs">
                          New
                        </ListItem.Tag>
                      )}
                      {event.visibility === 0 && (
                        <ListItem.Tag color="gray" variant="light" size="xs">
                          Hidden
                        </ListItem.Tag>
                      )}
                      {event.isHappeningNow && (
                        <ListItem.Tag color="warning" variant="light" size="xs">
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
                        />
                      )}
                    </div>
                  </ListItem>
                ))}
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
