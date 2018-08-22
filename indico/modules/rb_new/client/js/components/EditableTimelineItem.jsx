/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

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
        endHour: PropTypes.number.isRequired
    };

    constructor(props) {
        super(props);
        this.divRef = React.createRef();
        this.slotRef = React.createRef();
    }

    state = {
        editing: false
    };

    componentDidMount() {
        document.addEventListener('mouseup', this.mouseUpHandler);
    }

    componentWillUnmount() {
        document.removeEventListener('mouseup', this.mouseUpHandler);
    }

    calcSlotPosition(event) {
        const {startHour, endHour} = this.props;
        const el = this.divRef.current;
        const rect = el.getBoundingClientRect();
        const x = event.pageX - rect.x;
        const totalMinutes = (endHour - startHour) * 60;
        const minutes = (x / rect.width) * totalMinutes;

        const closestSlot = Math.round(minutes / RESOLUTION_MINUTES) * RESOLUTION_MINUTES;

        return {
            pixels: (closestSlot / totalMinutes) * rect.width,
            hours: Math.floor(closestSlot / 60) + startHour,
            minutes: closestSlot % 60
        };
    }

    mouseDownHandler = e => {
        const {hours, minutes, pixels} = this.calcSlotPosition(e);

        this.setState({
            editing: true,
            slotStartTime: `${hours}:${minutes}`,
            slotStartPx: pixels,
            slotEndPx: pixels + 15
        });
    };

    mouseMove = e => {
        const {editing} = this.state;

        if (editing) {
            const {hours, minutes, pixels} = this.calcSlotPosition(e);
            this.setState({
                slotEndTime: `${hours}:${minutes}`,
                slotEndPx: pixels
            });
        }
    };

    mouseUpHandler = e => {
        const {editing} = this.state;
        if (!editing) {
            return;
        }
        // this.setState({
        //     editing: false
        // });
        e.stopPropagation();
    };

    render() {
        const {editing, slotStartPx, slotEndPx, slotStartTime, slotEndTime} = this.state;
        console.log(this.slotRef.current)
        return (
            <TimelineItem {...this.props}>
                <div styleName="editable-timeline-canvas"
                     onMouseDown={this.mouseDownHandler}
                     onMouseMove={this.mouseMove}
                     onMouseLeave={this.mouseUpHandler}
                     ref={this.divRef}>
                    {editing && (
                        <div style={{left: slotStartPx, width: slotEndPx - slotStartPx}}
                             styleName="editable-timeline-slot"
                             ref={this.slotRef} />
                    )}
                </div>
                {editing && (
                    <>
                        <Popup context={this.slotRef.current} content={slotStartTime} position="bottom left" open />
                        <Popup context={this.slotRef.current} content={slotEndTime} position="top right" open />
                    </>
                )}
            </TimelineItem>
        );
    }
}
