// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import TimelineItem from './TimelineItem';

import './TimelineItem.module.scss';

const RESOLUTION_MINUTES = 15;

export default class EditableTimelineItem extends React.Component {
  static propTypes = {
    startHour: PropTypes.number.isRequired,
    endHour: PropTypes.number.isRequired,
    onAddSlot: PropTypes.func.isRequired,
    room: PropTypes.object.isRequired,
    setSelectable: PropTypes.func,
  };

  static defaultProps = {
    setSelectable: null,
  };

  state = {
    isEditing: false,
    canvasRef: null,
    slotRef: null,
    hintPosition: null,
  };

  componentDidMount() {
    document.addEventListener('mouseup', this.handleMouseUp);
  }

  componentWillUnmount() {
    document.removeEventListener('mouseup', this.handleMouseUp);
  }

  calcSlotPosition(event) {
    const {startHour, endHour} = this.props;
    const {canvasRef: el} = this.state;
    const rect = el.getBoundingClientRect();
    const x = event.pageX - rect.x;
    const totalMinutes = (endHour - startHour) * 60;
    const minutes = (x / rect.width) * totalMinutes;

    const closestSlot = Math.round(minutes / RESOLUTION_MINUTES) * RESOLUTION_MINUTES;

    return {
      pixels: (closestSlot / totalMinutes) * rect.width,
      hours: Math.floor(closestSlot / 60) + startHour,
      minutes: closestSlot % 60,
    };
  }

  setSelectable(state) {
    const {setSelectable} = this.props;
    if (setSelectable) {
      setSelectable(state);
    }
  }

  setNotEditing() {
    this.setSelectable(true);
    this.setState({
      isEditing: false,
      slotStartTime: null,
      slotEndTime: null,
      slotStartPx: null,
      slotEndPx: null,
    });
  }

  scheduleCancel() {
    this.setState({
      isCancelling: true,
      hintPosition: null,
    });

    setTimeout(() => {
      const {isCancelling} = this.state;
      if (!isCancelling) {
        return;
      }
      this.setNotEditing();
    }, 1000);
  }

  handleMouseDown = e => {
    const {hours, minutes, pixels} = this.calcSlotPosition(e);
    const slotStartTime = `${hours}:${minutes.toString().padStart(2, '0')}`;

    this.setSelectable(false);
    this.setState({
      isEditing: true,
      slotStartTime,
      slotStartPx: pixels,
      slotEndPx: pixels,
      slotOriginTime: slotStartTime,
      slotOriginPx: pixels,
      isCancelling: false,
    });
  };

  handleMouseMove = e => {
    const {isEditing, slotOriginTime, slotOriginPx, canvasRef, slotRef} = this.state;

    if (e.target !== canvasRef && e.target !== slotRef) {
      this.scheduleCancel();
      return;
    }

    this.setState({
      hintPosition: this.calcSlotPosition(e),
      isCancelling: false,
    });

    if (isEditing) {
      const {hours, minutes, pixels} = this.calcSlotPosition(e);
      const newTime = `${hours}:${minutes.toString().padStart(2, '0')}`;

      if (pixels - slotOriginPx > 0) {
        this.setState({
          slotStartTime: slotOriginTime,
          slotEndTime: newTime,
          slotStartPx: slotOriginPx,
          slotEndPx: pixels,
        });
      } else {
        this.setState({
          slotStartTime: newTime,
          slotEndTime: slotOriginTime,
          slotStartPx: pixels,
          slotEndPx: slotOriginPx,
        });
      }
    }
  };

  handleMouseUp = e => {
    const {isEditing, slotStartTime, slotEndTime, isCancelling} = this.state;
    const {onAddSlot, room} = this.props;

    e.stopPropagation();

    if (!isEditing || isCancelling) {
      return;
    }

    this.setNotEditing();

    if (slotStartTime === slotEndTime || !slotEndTime) {
      return;
    }

    onAddSlot({
      slotStartTime: `0${slotStartTime}`.slice(-5),
      slotEndTime: `0${slotEndTime}`.slice(-5),
      room,
    });
  };

  handleMouseEnter = e => {
    const {canvasRef} = this.state;

    // ignore event if we're on an occurrence
    if (e.target !== canvasRef) {
      return;
    }

    this.setState({
      hintPosition: this.calcSlotPosition(e),
      isCancelling: false,
    });
    e.stopPropagation();
  };

  handleMouseLeave = () => {
    this.scheduleCancel();
  };

  renderTimeLabels(width, slotStartTime, slotEndTime) {
    const {slotRef} = this.state;
    if (width === 0) {
      return (
        <Popup
          context={slotRef}
          content={Translate.string('Drag the mouse to create a booking')}
          position="top center"
          size="mini"
          open
        />
      );
    } else if (width < 50) {
      return (
        <Popup
          key={`${slotStartTime}:${slotEndTime}`}
          context={slotRef}
          content={`${slotStartTime} - ${slotEndTime}`}
          size="mini"
          position="bottom center"
          open
        />
      );
    } else {
      return (
        <>
          <Popup
            key={slotStartTime}
            context={slotRef}
            content={slotStartTime}
            position="top left"
            size="mini"
            open
          />
          <Popup
            key={slotEndTime}
            context={slotRef}
            content={slotEndTime}
            position="bottom right"
            size="mini"
            open
          />
        </>
      );
    }
  }

  setCanvasRef = ref => {
    this.setState({
      canvasRef: ref,
    });
  };

  setSlotRef = ref => {
    this.setState({
      slotRef: ref,
    });
  };

  render() {
    const {
      isEditing,
      slotStartPx,
      slotEndPx,
      slotStartTime,
      slotRef,
      slotEndTime,
      canvasRef,
      hintPosition,
    } = this.state;
    const {onAddSlot, setSelectable, ...restProps} = this.props;
    const {
      room: {canUserBook},
    } = this.props;
    const width = slotEndPx - slotStartPx;

    let tip;
    if (canUserBook) {
      tip = Translate.string('Tip: click and drag to book!');
    } else {
      tip = Translate.string('Tip: click and drag to pre-book!');
    }

    return (
      <TimelineItem
        {...restProps}
        onMouseDown={this.handleMouseDown}
        onMouseEnter={this.handleMouseEnter}
      >
        <div
          styleName="editable-timeline-canvas"
          onMouseMove={this.handleMouseMove}
          onMouseLeave={this.handleMouseLeave}
          ref={this.setCanvasRef}
        >
          {isEditing && (
            <div
              style={{left: slotStartPx, width: width || 15}}
              styleName="editable-timeline-slot"
              ref={this.setSlotRef}
            />
          )}
          {!isEditing && canvasRef && hintPosition !== null && (
            <Popup
              header={`${hintPosition.hours}:${hintPosition.minutes.toString().padStart(2, '0')}`}
              content={tip}
              position="top left"
              offset={[hintPosition.pixels, 0]}
              context={canvasRef}
              size="mini"
              styleName="editable-timeline-time-popup"
              open
            />
          )}
        </div>
        {isEditing && slotRef && this.renderTimeLabels(width, slotStartTime, slotEndTime)}
      </TimelineItem>
    );
  }
}
