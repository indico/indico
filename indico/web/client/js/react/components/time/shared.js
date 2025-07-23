import React, {useEffect, useMemo, useState} from 'react';

import {PluralTranslate} from 'indico/react/i18n';
import {Time, timeList} from 'indico/utils/time_value';

import './time.module.scss';

export const DEFAULT_STEP_SIZE = 15; // minutes
export const TIME_FORMAT_PLACEHOLDER = {
  '12h': '--:-- AM/PM',
  '24h': '--:--',
};

export function formatDuration(duration) {
  const durationInMins = duration.value;
  if (durationInMins < 60) {
    return PluralTranslate.string('{time} min', '{time} mins', durationInMins, {
      time: durationInMins,
    });
  }
  if (durationInMins % 30 === 0) {
    // 'Nice' hours like, either whole or half-hour
    const durationInHours = durationInMins / 60;
    return PluralTranslate.string('{time} hr', '{time} hrs', durationInHours, {
      time: durationInHours,
    });
  }
  // 'Ugly' hours, like 1:15, 1:05, won't display well as decimals
  return duration.toShortString();
}

export function getOptions(currentValue, startTime, step, minTime, maxTime, timeFormat) {
  return timeList({
    markCurrent: currentValue,
    startTime,
    step,
    minTime,
    maxTime,
    timeFormat,
  }).map(option => {
    const {label, time, duration, disabled} = option;

    const itemProps = {};

    if (disabled) {
      itemProps['aria-disabled'] = true;
    }

    return (
      <li role="option" data-value={label} data-time={time} key={time} {...itemProps}>
        <time dateTime={time} styleName="option-label">
          <span>{label}</span>
          {duration ? (
            <>
              {' '}
              <span>({formatDuration(duration)})</span>
            </>
          ) : null}
        </time>
      </li>
    );
  });
}

export function useOptions(currentValue, startTime, step, minTime, maxTime, timeFormat) {
  return useMemo(
    () => getOptions(currentValue, startTime, step, minTime, maxTime, timeFormat),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [startTime, step, minTime, maxTime, timeFormat]
  );
}

export function createBlurHandler(
  timeFormat,
  setInputValue,
  onChange,
  setNotice,
  getTimeClearedMessage,
  getTimeFormattedMessage
) {
  return ev => {
    // Reformat the value when user leaves the field

    const maybeTime = Time.fromString(ev.target.value);
    const maybeFixedValue = Number.isNaN(maybeTime.value)
      ? ''
      : maybeTime.toFormattedString(timeFormat);

    // Value was already fixed?
    if (maybeFixedValue === ev.target.value) {
      // Still call onChange even if value wasn't reformatted
      if (onChange) {
        onChange(maybeTime.isValid ? maybeTime.toString() : '');
      }
      return;
    }

    setInputValue(maybeFixedValue);

    // Call onChange with the final value
    if (onChange) {
      const finalTime = Time.fromString(maybeFixedValue, 'any');
      onChange(finalTime.isValid ? finalTime.toString() : '');
    }

    // Announce any changes to screen readers

    if (!maybeFixedValue) {
      setNotice(getTimeClearedMessage());
    } else {
      setNotice(getTimeFormattedMessage(maybeFixedValue));
    }
  };
}

export function useNotice() {
  const [notice, setNotice] = useState('');

  // Auto-clear notice
  useEffect(() => {
    if (!notice) {
      return;
    }

    const timer = setTimeout(() => {
      setNotice('');
    }, 10000);

    return () => clearTimeout(timer);
  }, [notice]);

  return [notice, setNotice];
}

export function useSyncInputWithProp(propValue, inputValue, setInputValue, timeFormat) {
  useEffect(
    () => {
      const propTime = Time.fromString(propValue, '24h');
      const internalTime = Time.fromString(inputValue, 'any');

      // Using Object.is() as value can also be NaN
      if (!Object.is(propTime.value, internalTime.value)) {
        setInputValue(propTime.toFormattedString(timeFormat));
      }
    },
    // The purpose of this hook is to sync the prop changes to the
    // input value *only* in cases where the prop was change without
    // first changing the input value. Therefore, the only valid
    // dependencies are the props. Adding anything from the local state
    // here would have undesired consequences.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [propValue, timeFormat]
  );
}

export function useInputValue(value, timeFormat) {
  return useState(value && Time.fromString(value, '24h').toFormattedString(timeFormat));
}
