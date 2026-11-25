// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react';

import {PluralTranslate, Translate} from 'indico/react/i18n';
import {Time, timeList} from 'indico/utils/time_value';

import './TimePicker.module.scss';

function formatDuration(duration) {
  const minutes = duration.value;
  if (minutes < 60) {
    return PluralTranslate.string('{count} min', '{count} min', minutes, {count: minutes});
  }
  if (minutes % 30 === 0) {
    const hours = minutes / 60;
    return PluralTranslate.string('{count} hour', '{count} hours', hours, {count: hours});
  }
  return duration.toShortString();
}

export default function TimePicker({
  label,
  value,
  timeFormat,
  min,
  max,
  step,
  firstOption,
  durationStart,
  required,
  disabled,
  onChange,
  onFocus,
  onBlur,
}) {
  const input = useRef(null);
  const list = useRef(null);
  const selectOnClick = useRef(false);
  const [listId] = useState(() => _.uniqueId('time-picker-options-'));
  const formattedValue = Time.fromString(value, '24h').toFormattedString(timeFormat);
  const [text, setText] = useState(formattedValue);
  const [expanded, setExpanded] = useState(false);
  const [filtering, setFiltering] = useState(false);
  const [activeTime, setActiveTime] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    setText(formattedValue);
    setError('');
    input.current.setCustomValidity('');
  }, [formattedValue]);

  const options = useMemo(
    () =>
      timeList({
        step,
        minTime: firstOption ?? min,
        maxTime: max,
        timeFormat,
        startTime: durationStart,
      }),
    [step, firstOption, min, max, timeFormat, durationStart]
  );
  const enteredTime = Time.fromString(text);
  const matching =
    !filtering || !text.trim()
      ? options
      : options.filter(
          option =>
            option.label.toLowerCase().startsWith(text.trim().toLowerCase()) ||
            option.value === enteredTime.value
        );
  const isOpen = expanded && !disabled && matching.length > 0;
  const selected =
    matching.find(option => option.time === activeTime) ??
    matching.find(option => option.value === enteredTime.value);
  const nearest = enteredTime.isValid
    ? (matching.find(option => option.value >= enteredTime.value) ?? matching.at(-1))
    : undefined;
  const optionId = option => `${listId}-${option.time.replace(':', '')}`;

  const close = useCallback(() => {
    setExpanded(false);
    setFiltering(false);
    setActiveTime(null);
  }, []);

  useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }
    // Semantic UI layers handle Escape during document capture.
    const handleEscape = event => {
      if (event.key === 'Escape' && event.target === input.current) {
        event.preventDefault();
        event.stopPropagation();
        close();
      }
    };
    window.addEventListener('keydown', handleEscape, true);
    return () => window.removeEventListener('keydown', handleEscape, true);
  }, [isOpen, close]);

  useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }
    const popup = list.current;
    popup.style.removeProperty('--available-height');
    const rect = input.current.getBoundingClientRect();
    const viewport = window.visualViewport;
    const below =
      (viewport?.height ?? window.innerHeight) + (viewport?.offsetTop ?? 0) - rect.bottom;
    const above = rect.top - (viewport?.offsetTop ?? 0);
    const aboveInput = below < popup.offsetHeight && above > below;
    popup.toggleAttribute('data-above', aboveInput);
    popup.toggleAttribute(
      'data-align-end',
      rect.left + popup.offsetWidth > document.documentElement.clientWidth
    );
    popup.style.setProperty('--available-height', `${Math.max(0, aboveInput ? above : below)}px`);
  }, [isOpen, matching.length]);

  const visibleTime = (selected ?? nearest)?.time;
  useLayoutEffect(() => {
    if (!isOpen || !visibleTime) {
      return;
    }
    const container = list.current;
    const option = container.querySelector(`[data-time="${visibleTime}"]`);
    const top = option.offsetTop;
    const bottom = top + option.offsetHeight;
    if (top < container.scrollTop) {
      container.scrollTop = top;
    } else if (bottom > container.scrollTop + container.clientHeight) {
      container.scrollTop = bottom - container.clientHeight;
    }
  }, [isOpen, visibleTime, matching.length]);

  function validationMessage(raw, time) {
    if (!raw.trim()) {
      return required ? Translate.string('Enter a time.') : '';
    }
    if (!time.isValid) {
      return Translate.string('Enter a valid time, for example {time}.', {
        time: new Time(13 * 60 + 30).toFormattedString(timeFormat),
      });
    }
    if (time.value < Time.fromString(min, '24h').value) {
      return Translate.string('Enter a time at or after {time}.', {
        time: Time.fromString(min, '24h').toFormattedString(timeFormat),
      });
    }
    if (time.value > Time.fromString(max, '24h').value) {
      return Translate.string('Enter a time at or before {time}.', {
        time: Time.fromString(max, '24h').toFormattedString(timeFormat),
      });
    }
    return '';
  }

  function commit(raw) {
    const time = Time.fromString(raw);
    const message = validationMessage(raw, time);
    input.current.setCustomValidity(message);
    setError(message);
    if (!message) {
      setText(time.toFormattedString(timeFormat));
      const next = time.toSafeString();
      if (next !== value) {
        onChange(next);
      }
    }
    close();
  }

  function handleEdit(event) {
    const raw = event.target.value;
    const message = validationMessage(raw, Time.fromString(raw));
    event.target.setCustomValidity(message);
    setText(raw);
    if (error) {
      setError(message);
    }
    setFiltering(true);
    setActiveTime(null);
    setExpanded(true);
  }

  function handleKeyDown(event) {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowUp': {
        if (!matching.length) {
          return;
        }
        event.preventDefault();
        setExpanded(true);
        if (!event.altKey) {
          const selectedIndex = matching.indexOf(selected);
          const offset = event.key === 'ArrowDown' ? 1 : -1;
          const nextIndex =
            selectedIndex === -1
              ? nearest
                ? matching.indexOf(nearest)
                : offset === 1
                  ? 0
                  : matching.length - 1
              : (selectedIndex + offset + matching.length) % matching.length;
          setActiveTime(matching[nextIndex].time);
        }
        break;
      }
      case 'Enter':
        if (isOpen || text !== formattedValue) {
          event.preventDefault();
          commit(activeTime ? (selected?.time ?? text) : text);
        }
        break;
    }
  }

  return (
    <ind-time-picker styleName="picker" open={isOpen ? '' : undefined}>
      <div styleName="control">
        <label styleName="field">
          <span styleName="field-label">{label}</span>
          <input
            ref={input}
            type="text"
            name="time"
            role="combobox"
            autoComplete="off"
            aria-autocomplete="list"
            aria-controls={listId}
            aria-expanded={isOpen}
            aria-activedescendant={isOpen && selected ? optionId(selected) : undefined}
            spellCheck={false}
            value={text}
            placeholder={timeFormat === '12h' ? '--:-- AM/PM' : '--:--'}
            required={required}
            disabled={disabled}
            onChange={handleEdit}
            onFocus={event => {
              event.target.select();
              onFocus?.(event);
            }}
            onMouseDown={event => {
              selectOnClick.current = event.currentTarget !== document.activeElement;
            }}
            onClick={event => {
              if (selectOnClick.current) {
                const target = event.currentTarget;
                requestAnimationFrame(() => {
                  if (document.activeElement === target) {
                    target.select();
                  }
                });
                selectOnClick.current = false;
              }
              setFiltering(false);
              setExpanded(true);
            }}
            onBlur={event => {
              commit(event.target.value);
              onBlur?.(event);
            }}
            onInvalid={event => setError(event.target.validationMessage)}
            onKeyDown={handleKeyDown}
          />
        </label>
        <ul
          ref={list}
          id={listId}
          role="listbox"
          aria-label={label}
          hidden={!isOpen}
          styleName="options"
        >
          {matching.map(option => (
            <li
              key={option.time}
              id={optionId(option)}
              role="option"
              data-time={option.time}
              aria-selected={option === selected}
              onMouseDown={event => event.preventDefault()}
              onClick={() => commit(option.time)}
            >
              {option.label}
              {option.duration && (
                <span styleName="duration"> ({formatDuration(option.duration)})</span>
              )}
            </li>
          ))}
        </ul>
      </div>
      <output styleName="error">{error}</output>
    </ind-time-picker>
  );
}

TimePicker.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  timeFormat: PropTypes.oneOf(['12h', '24h']).isRequired,
  min: PropTypes.string,
  max: PropTypes.string,
  step: PropTypes.number,
  firstOption: PropTypes.string,
  durationStart: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
};

TimePicker.defaultProps = {
  min: '00:00',
  max: '23:59',
  step: 15,
  firstOption: undefined,
  durationStart: undefined,
  required: false,
  disabled: false,
  onFocus: undefined,
  onBlur: undefined,
};
