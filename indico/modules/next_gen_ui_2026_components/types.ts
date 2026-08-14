// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {IndicoPaletteColor, LegacyColor} from './tokens';

export interface CategorySimple {
  id: number;
  title: string;
}

export interface Category {
  id: number;
  title: string;
  isProtected: boolean;
  hasEvents: boolean;
  hasChildren: boolean;
  deepCategoryCount: number;
  deepEventCount: number;
  canAccess: boolean;
  canCreateEvents: boolean;
  canProposeEvents: boolean;
  canManage: boolean;
  path: CategorySimple[];
  parentPath: CategorySimple[];
  displayURL?: string;
  description?: string;
}

export interface Event {
  id: number;
  title: string;
  verbosedTitle: string;
  seriesLabel: string;
  url: string;
  date: string;
  isRecent: boolean;
  isHappeningNow: boolean;
  visibility: number;
  isProtected: boolean;
  label: string;
  labelColor: IndicoPaletteColor | LegacyColor;
  isFavorite: boolean;
}

export interface EventsMonth {
  name: string;
  isCurrent: boolean;
  events: Event[];
}

export interface Manager {
  id: number;
  name: string;
  email: string;
  avatarURL: string;
  profileURL: string;
}

export interface NewsItem {
  id: number;
  title: string;
  content: string;
  createdDt: string;
  anchor: string;
  url: string;
}

export interface UpcomingEvent {
  id: number;
  title: string;
  isHappeningNow: boolean;
  url: string;
  startDt: string;
  endDt: string;
}

export interface CategoryViewData {
  availableYears: number[];
  hasHiddenEvents: boolean;
  managers: Manager[];
  isFlat: boolean;
  pendingEventMoves: number;
  showPastEvents: boolean;
  showFutureEvents: boolean;
  eventCount: number;
  eventsByMonth: EventsMonth;
  futureEventsByMonth: EventsMonth;
  pastEventsByMonth: EventsMonth;
  futureEventCount: number;
  pastEventCount: number;
  news: NewsItem[];
  upcomingEvents: UpcomingEvent[];
}
