// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiEventListURL from 'indico-url:categories.api_event_list';

import React from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

import {Button} from '../button/Button';
import {Indicator} from '../indicator/Indicator';
import {TimelineItem} from '../timeline/Timeline';
import {CategoryEventListWithMetaData, Event, EventsMonth} from '../types';
import {YearPicker} from '../yearPicker/YearPicker';

import {FavoriteButton} from './FavoriteButton';
import {ListItem} from './ListItem';

import './EventList.module.scss';

interface EventListProps {
  categoryId: number;
  isFlat?: boolean;
  viewData: CategoryEventListWithMetaData;
}
export function EventList({categoryId, isFlat, viewData}: EventListProps) {
  const [selectedYear, setSelectedYear] = React.useState<number>(new Date().getFullYear());

  const {
    data: eventListData,
    loading: fetchingList,
    reFetch: fetchEventList,
  } = useIndicoAxios(
    apiEventListURL({
      category_id: String(categoryId),
      year: String(selectedYear),
      flat: isFlat ? 1 : 0,
    }),
    {
      camelize: true,
      manual: true,
    }
  );

  const isFirstRender = React.useRef(true);

  React.useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    fetchEventList({
      url: apiEventListURL({
        category_id: String(categoryId),
        year: String(selectedYear),
        flat: isFlat ? 1 : 0,
      }),
    }).catch((err: {code?: string}) => {
      if (err?.code !== 'ERR_CANCELED') {
        console.error('Failed to fetch event list', err);
      }
    });
  }, [selectedYear, categoryId, isFlat, fetchEventList]);

  const activeData = eventListData ?? viewData?.eventListData;

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

  if (
    !viewData ||
    !activeData ||
    (events.length === 0 && futureEventsCount === 0 && pastEventsCount === 0)
  ) {
    return null;
  }

  const listItem = (event: Event, month: EventsMonth) => (
    <ListItem styleName="event-list-item" key={event.id + month.name} href={event.url}>
      <div styleName="event-list-item-start-section">
        <ListItem.Tag
          color="primary"
          variant="transparent"
          size="sm"
          textWeight="regular"
          styleName="event-list-item-date-tag"
        >
          {event.date}
        </ListItem.Tag>
        <ListItem.Header title={event.verbosedTitle}>{event.verbosedTitle}</ListItem.Header>

        {event.seriesLabel && <ListItem.Details>{event.seriesLabel}</ListItem.Details>}
      </div>
      <div styleName="event-list-item-tag-section">
        {event.label && (
          <ListItem.Tag color={event.labelColor} size="xs" styleName="event-list-item-label">
            {event.label}
          </ListItem.Tag>
        )}
        {event.visibility === 0 && (
          <ListItem.Icon
            icon="fas:eye-slash"
            color="gray"
            size="sm"
            variant="transparent"
            ariaLabel="Hidden Event"
            title={Translate.string('Hidden')}
          />
        )}

        {event.isProtected && (
          <ListItem.Icon
            icon="fas:shield-halved"
            color="error"
            size="sm"
            variant="transparent"
            ariaLabel="Protected Category"
            title={Translate.string('Protected')}
          />
        )}
      </div>
    </ListItem>
  );

  const expandButton = (expanded: boolean, count: number, onClick: () => void) => (
    <Button
      styleName="event-list-show-more"
      variant="transparent"
      color="primary"
      size="sm"
      disabled={fetchingList}
      icon={expanded ? 'fas:chevron-up' : 'fas:chevron-down'}
      iconPosition="right"
      onClick={onClick}
    >
      <span>
        {expanded
          ? Translate.string('Show less ({0})', [count])
          : Translate.string('Show more ({0})', [count])}
      </span>
    </Button>
  );
  return (
    <div styleName="event-list">
      <YearPicker
        yearList={viewData.availableYears}
        selectedYear={selectedYear}
        onYearSelect={setSelectedYear}
        styleName="event-list-year-picker"
      />

      {futureEventsCount > 0 &&
        expandButton(futureEventsExpanded, futureEventsCount, () =>
          setUserFutureExpanded(!futureEventsExpanded)
        )}

      {events.map(month => (
        <TimelineItem key={month.name} styleName="event-list-month">
          <TimelineItem.Title dotColor="primary">{month.name.split(' ')[0]}</TimelineItem.Title>
          <TimelineItem.Content>
            {month.events.map((event: Event) =>
              event.isRecent ? (
                <Indicator
                  key={event.id + event.date}
                  styleName="event-list-item-wrapper"
                  size="sm"
                  title={Translate.string('New')}
                >
                  <FavoriteButton
                    type="event"
                    id={event.id}
                    favorited={event.isFavorite}
                    styleName="event-list-item-favorite-icon"
                  />
                  {listItem(event, month)}
                </Indicator>
              ) : (
                <div key={event.id + event.date} styleName="event-list-item-wrapper">
                  <FavoriteButton
                    type="event"
                    id={event.id}
                    favorited={event.isFavorite}
                    styleName="event-list-item-favorite-icon"
                  />
                  {listItem(event, month)}
                </div>
              )
            )}
          </TimelineItem.Content>
        </TimelineItem>
      ))}

      {pastEventsCount > 0 &&
        expandButton(pastEventsExpanded, pastEventsCount, () =>
          setUserPastExpanded(!pastEventsExpanded)
        )}
    </div>
  );
}
