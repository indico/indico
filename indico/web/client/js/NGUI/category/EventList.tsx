// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiEventListURL from 'indico-url:categories.api_event_list';

import React, {useEffect, useMemo, useRef, useState} from 'react';

import {Button, FavoriteButton, List, ListItem, TimelineItem, YearPicker} from 'indico/NGUI';
import {CategoryEventListWithMetaData, Event} from 'indico/NGUI/types';
import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

import './EventList.module.scss';

export interface ExpandButtonProps {
  wasExpanded: boolean;
  count: number;
  onClick: () => void;
  reversedChevron?: boolean;
  disabled?: boolean;
}

export function ExpandButton({
  wasExpanded,
  count,
  onClick,
  reversedChevron = false,
  disabled = false,
}: ExpandButtonProps) {
  return (
    <Button
      styleName="event-list-show-more"
      variant="transparent"
      color="primary"
      size="sm"
      disabled={disabled}
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
}
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

  return (
    <div styleName="event-list-wrapper">
      <YearPicker
        yearList={viewData.availableYears}
        selectedYear={selectedYear}
        onYearSelect={setSelectedYear}
        styleName="event-list-year-picker"
      />

      {futureEventsCount > 0 && (
        <ExpandButton
          wasExpanded={futureEventsExpanded}
          count={futureEventsCount}
          onClick={() => setUserFutureExpanded(!futureEventsExpanded)}
          disabled={fetchingList}
        />
      )}
      <div role="list" styleName="event-list">
        {events.map(month => (
          <TimelineItem role="listitem" key={month.name}>
            <TimelineItem.Title dotColor="primary">{month.name.split(' ')[0]}</TimelineItem.Title>
            <TimelineItem.Content>
              <List>
                {month.events.map((event: Event) => (
                  <ListItem
                    styleName="event-list-item event-list-item-spacing"
                    key={event.id + month.name}
                    contentProps={{href: event.url}}
                    marker={
                      <FavoriteButton
                        type="event"
                        id={event.id}
                        favorited={event.isFavorite}
                        styleName="event-list-item-favorite-icon"
                      />
                    }
                  >
                    {event.isRecent && <ListItem.Indicator size="xs" />}
                    <ListItem.Tag
                      color="primary"
                      variant="transparent"
                      size="sm"
                      textWeight="regular"
                      styleName="event-list-item-date-tag"
                    >
                      {event.date}
                    </ListItem.Tag>
                    <ListItem.Header title={event.verbosedTitle}>
                      {event.verbosedTitle}
                    </ListItem.Header>
                    {event.seriesLabel && (
                      <ListItem.Details styleName="event-list-item-series-label">
                        {event.seriesLabel}
                      </ListItem.Details>
                    )}
                    <div styleName="event-list-item-tag-section">
                      {event.label && (
                        <ListItem.Tag
                          color={event.labelColor}
                          size="xs"
                          styleName="event-list-item-label"
                        >
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
                ))}
              </List>
            </TimelineItem.Content>
          </TimelineItem>
        ))}
      </div>

      {pastEventsCount > 0 && (
        // expandButton(pastEventsExpanded, pastEventsCount, () =>
        //   setUserPastExpanded(!pastEventsExpanded)
        // )
        <ExpandButton
          wasExpanded={pastEventsExpanded}
          count={pastEventsCount}
          onClick={() => setUserPastExpanded(!pastEventsExpanded)}
          disabled={fetchingList}
        />
      )}
    </div>
  );
}
