// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef} from 'react';

import {PluralTranslate, Translate} from 'indico/react/i18n';
import {position, verticalTooltipPositionStrategy} from 'indico/utils/positioning';

export default function CategoryStats({category}) {
  const catCount = category.deep_category_count ?? 0;
  const eventCount = category.deep_event_count ?? 0;
  const detailsRef = useRef(null);
  const contentRef = useRef(null);
  const stopPositioningRef = useRef(null);

  const stopPositioning = () => {
    stopPositioningRef.current?.();
    stopPositioningRef.current = null;
  };

  useEffect(() => stopPositioning, []);

  const handleToggle = () => {
    stopPositioning();
    detailsRef.current.removeAttribute('data-positioned');
    if (!detailsRef.current.open) {
      return;
    }
    const abortController = new AbortController();
    let stopPositionUpdates = position(
      contentRef.current,
      detailsRef.current,
      verticalTooltipPositionStrategy,
      () => detailsRef.current?.toggleAttribute('data-positioned', true)
    );
    // The positioning code only follows window scrolling; the category list scrolls on its own
    document.addEventListener(
      'scroll',
      () => {
        stopPositionUpdates();
        stopPositionUpdates = position(
          contentRef.current,
          detailsRef.current,
          verticalTooltipPositionStrategy
        );
      },
      {capture: true, passive: true, signal: abortController.signal}
    );
    // Some browsers (e.g. Firefox and Safari on macOS) do not focus the summary on click,
    // so closing on blur alone would not catch clicks outside
    document.addEventListener(
      'pointerdown',
      evt => {
        if (!detailsRef.current.contains(evt.target)) {
          detailsRef.current.open = false;
        }
      },
      {capture: true, signal: abortController.signal}
    );
    stopPositioningRef.current = () => {
      abortController.abort();
      stopPositionUpdates();
    };
  };

  const handleKeyDown = evt => {
    if (evt.key !== 'Escape' || !detailsRef.current.open) {
      return;
    }
    // Keep Escape from also closing the navigator dialog
    evt.preventDefault();
    detailsRef.current.open = false;
  };

  const handleBlur = evt => {
    if (evt.relatedTarget && !detailsRef.current.contains(evt.relatedTarget)) {
      detailsRef.current.open = false;
    }
  };

  return (
    <span className="stats">
      <span className="icon-list" aria-hidden="true" />
      <span aria-hidden="true">
        {catCount} | {eventCount}
      </span>
      <details
        ref={detailsRef}
        className="stats-details"
        onToggle={handleToggle}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
      >
        <summary>
          <i className="icon-info" aria-hidden="true" />
          <span>
            <Translate>Category statistics</Translate>
          </span>
        </summary>
        <span ref={contentRef} className="stats-details-content">
          {PluralTranslate.string('{count} category', '{count} categories', catCount, {
            count: catCount,
          })}
          <br />
          {PluralTranslate.string('{count} event', '{count} events', eventCount, {
            count: eventCount,
          })}
        </span>
      </details>
    </span>
  );
}

CategoryStats.propTypes = {
  category: PropTypes.shape({
    deep_category_count: PropTypes.number,
    deep_event_count: PropTypes.number,
  }).isRequired,
};
