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

import React from 'react';
import moment from 'moment';
import PropTypes from 'prop-types';
import shortid from 'shortid';
import {Icon, Button} from 'semantic-ui-react';
import {ANCHOR_RIGHT} from 'react-dates/constants';
import {Translate} from 'indico/react/i18n';
import {DateRangePicker} from 'indico/react/components';
import {serializeDate} from 'indico/utils/date';


export default class NonBookablePeriods extends React.Component {
    static propTypes = {
        onFocus: PropTypes.func.isRequired,
        onBlur: PropTypes.func.isRequired,
        onChange: PropTypes.func.isRequired,
        value: PropTypes.array,
    };

    static defaultProps = {
        value: []
    };

    handleAddDates = () => {
        const {value, onChange} = this.props;
        onChange([
            ...value,
            {
                startDt: serializeDate(moment()),
                endDt: serializeDate(moment()),
                key: shortid.generate()
            }
        ]);
        this.setTouched();
    };

    handleRemoveDates = (key) => {
        const {value, onChange} = this.props;
        onChange([...value.filter((dA) => dA.key !== key)]);
        this.setTouched();
    };

    handleDatesChange = ({startDate, endDate}, key) => {
        const {value, onChange} = this.props;
        onChange(value.map(v => {
            if (v.key === key) {
                return {...v, startDt: serializeDate(startDate), endDt: serializeDate(endDate)};
            } else {
                return v;
            }
        }));
        this.setTouched();
    };

    setTouched = () => {
        // pretend focus+blur to mark the field as touched in case an action changes
        // the data without actually involving focus and blur of a form element
        const {onFocus, onBlur} = this.props;
        onFocus();
        onBlur();
    };

    renderEntry = (dateRangeItem) => {
        const {startDt, endDt, key} = dateRangeItem;
        return (
            <div key={key} className="flex-container">
                <DateRangePicker small
                                 minimumNights={0}
                                 anchorDirection={ANCHOR_RIGHT}
                                 startDate={startDt === null ? null : moment(startDt)}
                                 endDate={endDt === null ? null : moment(endDt)}
                                 onDatesChange={(dates) => this.handleDatesChange(dates, key)} />
                <Icon floated="right" name="remove" className="delete-button" onClick={() => this.handleRemoveDates(key)} />
            </div>
        );
    };

    render() {
        const {value} = this.props;
        return (
            <>
                <Button type="button"
                        className="room-edit-modal-add-btn"
                        icon labelPosition="left"
                        onClick={this.handleAddDates}>
                    <Icon name="plus" />
                    <Translate>Add new Nonbookable Periods</Translate>
                </Button>
                {value && value.map((dateRangeItem) => this.renderEntry(dateRangeItem))}
                {value.length === 0 && <div><Translate>No non-bookable periods found</Translate></div>}
            </>
        );
    }
}
