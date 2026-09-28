// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiEventListURL from 'indico-url:categories.api_event_list';

import React, {useEffect, useMemo, useRef, useState} from 'react';

import {Button} from 'indico/NGUI/button/Button';
import {FavoriteButton} from 'indico/NGUI/button/FavoriteButton';
import {Indicator} from 'indico/NGUI/indicator/Indicator';
import {ListItem} from 'indico/NGUI/list/ListItem';
import {TimelineItem} from 'indico/NGUI/timeline/Timeline';
import {CategoryEventListWithMetaData, Event, EventsMonth} from 'indico/NGUI/types';
import {YearPicker} from 'indico/NGUI/yearPicker/YearPicker';
import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

import './EventList.module.scss';

interface EventListProps {
  categoryId: number;
  isFlat?: boolean;
  viewData: CategoryEventListWithMetaData;
}
export function EventList({categoryId, isFlat, viewData}: EventListProps) {
  const [selectedYear, setSelectedYear] = React.useState<number>(new Date().getFullYear());
  const eventListURL = apiEventListURL({
    category_id: categoryId,
    year: selectedYear,
    flat: isFlat ? 1 : 0,
  });

  const {
    data: eventListData,
    loading: fetchingList,
    reFetch: fetchEventList,
  } = useIndicoAxios(eventListURL, {camelize: true, manual: true});

  const isFirstRender = useRef(true);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    fetchEventList({url: eventListURL});
  }, [isFlat, fetchEventList, eventListURL]);

  const [userFutureExpanded, setUserFutureExpanded] = useState<boolean | null>(null);
  const [userPastExpanded, setUserPastExpanded] = useState<boolean | null>(null);

  const futureEventsExpanded = userFutureExpanded ?? viewData.showFutureEvents;
  const pastEventsExpanded = userPastExpanded ?? viewData.showPastEvents;

  const activeData = eventListData ?? viewData.eventListData;

  const futureEventsCount = activeData?.futureEventCount ?? 0;
  const pastEventsCount = activeData?.pastEventCount ?? 0;

  const events = useMemo(() => {
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

  const expandButton = (
    wasExpanded: boolean,
    count: number,
    onClick: () => void,
    reversedChevron = false
  ) => (
    <Button
      styleName="event-list-show-more"
      variant="transparent"
      color="primary"
      size="sm"
      disabled={fetchingList}
      icon={
        (!wasExpanded && reversedChevron) || (wasExpanded && !reversedChevron)
          ? 'fas:chevron-up'
          : 'fas:chevron-down'
      }
      iconPosition="right"
      onClick={onClick}
    >
      <span>
        {wasExpanded
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
        expandButton(
          futureEventsExpanded,
          futureEventsCount,
          () => setUserFutureExpanded(!futureEventsExpanded),
          true
        )}

      {events.map(month => (
        <TimelineItem key={month.name} styleName="event-list-month">
          <TimelineItem.Title dotColor="primary">{month.name.split(' ')[0]}</TimelineItem.Title>
          <TimelineItem.Content>
            {month.events.map((event: Event) =>
              event.isRecent ? (
                <Indicator
                  key={event.id}
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
                <div key={event.id} styleName="event-list-item-wrapper">
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
