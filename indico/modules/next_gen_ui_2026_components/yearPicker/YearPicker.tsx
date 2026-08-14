// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Button} from '../button/Button';
import './YearPicker.module.scss';
import {sharedClassName} from '../utils';

interface CustomYearPickerProps {
  yearList: number[];
  selectedYear?: number | null;
  onYearSelect: (year: number) => void;
}

export type YearPickerProps = CustomYearPickerProps & React.HTMLAttributes<HTMLDivElement>;

export function YearPicker({
  yearList,
  selectedYear,
  onYearSelect,
  ...nativeProps
}: YearPickerProps) {
  const yearListRef = React.useRef<HTMLDivElement | null>(null);
  const currentYearIdx = yearList.findIndex(year => year === selectedYear);
  const reachedLastYear = currentYearIdx >= yearList.length - 1;
  const yearWidth = 85;

  const scrollToYear = (yearIndex: number, behavior: ScrollBehavior = 'instant') => {
    if (!yearListRef.current) {
      return;
    }
    const barWidth = yearListRef.current.clientWidth;
    const left = yearIndex * yearWidth - barWidth / 2 + yearWidth / 2;
    yearListRef.current.scrollTo({left, behavior});
  };

  const navigateToYear = (yearIndex: number, behavior: ScrollBehavior = 'smooth') => {
    scrollToYear(yearIndex, behavior);
    onYearSelect(yearList[yearIndex]);
  };

  const changeYear = (yearDelta: number, behavior: ScrollBehavior = 'smooth') => {
    const directionSign = Math.sign(yearDelta);
    const newYear =
      directionSign === 1
        ? Math.min(currentYearIdx + yearDelta, yearList.length - 1)
        : Math.max(currentYearIdx + yearDelta, 0);
    navigateToYear(newYear, behavior);
  };

  return (
    <div
      {...nativeProps}
      styleName="year-picker"
      className={sharedClassName(nativeProps.className)}
    >
      <Button
        variant="transparent"
        icon="fas:chevron-left"
        iconOnly
        size="sm"
        styleName="year-picker-chevron-button"
        aria-label="Previous years"
        onClick={() => changeYear(-1)}
        disabled={currentYearIdx === 0}
      />
      <div styleName="year-list" ref={yearListRef}>
        {yearList.map(year => (
          <Button
            key={year}
            variant="transparent"
            textWeight="regular"
            styleName="year-picker-year-button"
            onClick={() => {
              onYearSelect(year);
            }}
            active={selectedYear === year}
          >
            {year}
          </Button>
        ))}
      </div>
      <Button
        variant="transparent"
        icon="fas:chevron-right"
        iconOnly
        size="sm"
        styleName="year-picker-chevron-button"
        aria-label="Next years"
        onClick={() => changeYear(1)}
        disabled={reachedLastYear}
      />
    </div>
  );
}
