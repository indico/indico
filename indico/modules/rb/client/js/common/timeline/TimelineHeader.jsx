// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.


import React from 'react';
import PropTypes from 'prop-types';
import TimelineLegend from './TimelineLegend';
import {legendLabelShape} from '../../props';
import DateNavigator from './DateNavigator';


export default class TimelineHeader extends React.Component {
    static propTypes = {
        datePicker: PropTypes.object.isRequired,
        legendLabels: PropTypes.arrayOf(legendLabelShape).isRequired,
        onDateChange: PropTypes.func.isRequired,
        onModeChange: PropTypes.func.isRequired,
        disableDatePicker: PropTypes.bool,
        isLoading: PropTypes.bool
    };

    static defaultProps = {
        isLoading: false,
        disableDatePicker: false
    };

    render() {
        const {disableDatePicker, isLoading, legendLabels, onModeChange, onDateChange, datePicker} = this.props;
        return (
            <TimelineLegend labels={legendLabels} aside={(
                <DateNavigator {...datePicker}
                               isLoading={isLoading}
                               disabled={disableDatePicker || isLoading}
                               onDateChange={onDateChange}
                               onModeChange={onModeChange} />
            )} />
        );
    }
}
