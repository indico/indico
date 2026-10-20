// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {IndicoPaletteColor, LegacyColor} from 'indico/NGUI/tokens';

export interface Category {
  id: number;
  title: string;
  description: string;
  logoURL: string | null;
  isFlat: boolean;
  isRoot: boolean;
  hasChildren: boolean;
}

export interface CategoryChildMetadata {
  id: number;
  title: string;
  isProtected: boolean;
  deepCategoryCount: number;
  deepEventCount: number;
  displayURL?: string;
}

export interface Event {
  id: number;
  title: string;
  verboseTitle: string;
  seriesLabel: string;
  url: string;
  date: string;
  isRecent: boolean;
  isHappeningNow: boolean;
  visibility: number;
  isProtected: boolean;
  label: string;
  labelColor: IndicoPaletteColor | LegacyColor;
  isFavorite: boolean | null;
}

export interface EventsMonth {
  name: string;
  isCurrent: boolean;
  events: Event[];
}

export interface EventListData {
  isFlat: boolean;
  eventCount: number;
  eventsByMonth: EventsMonth[];
  futureEventsByMonth: EventsMonth[];
  pastEventsByMonth: EventsMonth[];
  futureEventCount: number;
  pastEventCount: number;
}
export interface CategoryEventListWithMetaData {
  availableYears: number[];
  displayedYear: number;
  hasHiddenEvents: boolean;
  isFlat: boolean;
  pendingEventMoves: number;
  showPastEvents: boolean;
  showFutureEvents: boolean;
  eventListData: EventListData;
}
