// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import Overridable from 'react-overridable';
import {Button, Icon, Segment} from 'semantic-ui-react';
import {Param, Translate} from 'indico/react/i18n';
import {toMoment} from 'indico/utils/date';
import {renderRecurrence} from '../util';

import './TimeInformation.module.scss';

function TimeInformation({
  recurrence,
  dates: {startDate, endDate},
  timeSlot,
  onClickOccurrences,
  occurrenceCount,
}) {
  const mStartDate = toMoment(startDate);
  const mEndDate = endDate ? toMoment(endDate) : null;
  let timeInfo = null;

  if (timeSlot) {
    const {startTime, endTime} = timeSlot;
    const mStartTime = toMoment(startTime, 'HH:mm');
    const mEndTime = endTime ? toMoment(endTime, 'HH:mm') : null;
    timeInfo = (
      <Segment>
        <Icon name="clock" />
        <strong>{mStartTime.format('LT')}</strong>
        {' → '}
        <strong>{mEndTime.format('LT')}</strong>
      </Segment>
    );
  }
  return (
    <div styleName="booking-time-info">
      <Segment.Group>
        <Segment color="teal">
          <div>
            <Icon name="calendar outline" />
            {mEndDate && !mStartDate.isSame(mEndDate, 'day') ? (
              <Translate>
                <Param name="startDate" wrapper={<strong />} value={mStartDate.format('L')} /> to{' '}
                <Param name="endDate" wrapper={<strong />} value={mEndDate.format('L')} />
              </Translate>
            ) : (
              <strong>{mStartDate.format('L')}</strong>
            )}
          </div>
        </Segment>
        {timeInfo}
        <Segment>
          <div styleName="occurrences-details">
            <div>
              <Icon name="list" />
              <strong>
                {renderRecurrence(recurrence, false)}
                {occurrenceCount > 1 && (
                  <>
                    {', '}
                    <Translate>
                      <Param name="count" value={occurrenceCount} /> occurrences
                    </Translate>
                  </>
                )}
              </strong>
            </div>
            <Button size="small" basic color="teal" onClick={onClickOccurrences}>
              <Icon name="calendar outline" />
              <Translate>See on timeline</Translate>
            </Button>
          </div>
        </Segment>
      </Segment.Group>
    </div>
  );
}

TimeInformation.propTypes = {
  recurrence: PropTypes.object.isRequired,
  dates: PropTypes.shape({
    startDate: PropTypes.string.isRequired,
    endDate: PropTypes.string,
  }).isRequired,
  timeSlot: PropTypes.shape({
    startTime: PropTypes.string,
    endTime: PropTypes.string,
  }),
  onClickOccurrences: PropTypes.func.isRequired,
  occurrenceCount: PropTypes.number,
};

TimeInformation.defaultProps = {
  timeSlot: null,
  occurrenceCount: 0,
};

export default Overridable.component('TimeInformation', TimeInformation);
